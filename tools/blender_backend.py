# SPDX-License-Identifier: Apache-2.0
"""Headless Blender adapter; consumes prepared plain JSON only."""

import hashlib
import json
import platform

import bpy
from mathutils import Matrix, Vector

from tools.geometry import primitive_mesh
from tools.runtime import check_blender_version


def matrix(frame):
    result = Matrix(frame["rotation"]).to_4x4()
    result.translation = Vector(frame["position_m"])
    return result


def frame(value):
    return {"position_m":list(value.translation),"rotation":[list(row) for row in value.to_3x3().normalized()]}


def ordered(bodies):
    pending = {b["id"]:b for b in bodies};result=[];done=set()
    while pending:
        ready = sorted(id for id,b in pending.items() if b["parent"] is None or b["parent"] in done)
        if not ready: raise ValueError("Unresolved body hierarchy")
        for id in ready:result.append(pending.pop(id));done.add(id)
    return result


def mesh_object(name,vertices,faces,collection,material=None):
    mesh = bpy.data.meshes.new(name+".mesh")
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj = bpy.data.objects.new(name,mesh);collection.objects.link(obj)
    if material is not None: mesh.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    return obj


class SkeletonBackend:
    def __init__(self,prepared):
        check_blender_version(bpy.app.version_string,bpy.app.build_hash.decode())
        self.prepared = prepared
        self.profile = prepared["sources"]["profile"]
        self.scene_source = prepared["sources"]["review-scene"]
        self.height = self.profile["stature_m"]
        self.bodies = ordered(self.profile["structures"])
        self.index = {b["id"]:b for b in self.bodies}
        self.primitive_index = {g['id']:g for b in self.bodies for g in b['geometry']}
        for obj in list(bpy.data.objects): bpy.data.objects.remove(obj,do_unlink=True)
        for collection in list(bpy.data.collections): bpy.data.collections.remove(collection)
        self.collections = {}
        for name in ("Anatomy","Controls","Humanoid","Review"):
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
            self.collections[name] = collection
        self.material = bpy.data.materials.new("skeletal-reference")
        self.material.diffuse_color = (*self.scene_source["shading"]["bone_color"],1)
        self.meshes,self.carriers,self.semantic,self.targets = {},{},{},{}
        self.world_root=bpy.data.objects.new('WorldRoot',None)
        self.collections['Controls'].objects.link(self.world_root)
        self.rig = self.make_rig()
        self.rig.parent=self.world_root
        for body in self.bodies:
            id = body["id"]
            if body["representation"]=="omitted": continue
            carrier = bpy.data.objects.new("body."+id,None)
            carrier.empty_display_type='PLAIN_AXES';carrier.empty_display_size=.01*self.height
            self.collections["Anatomy"].objects.link(carrier)
            constraint = carrier.constraints.new('COPY_TRANSFORMS')
            constraint.target=self.rig;constraint.subtarget=id
            constraint.target_space='WORLD';constraint.owner_space='WORLD'
            self.carriers[id] = carrier
            for primitive in body["geometry"]:
                if primitive["type"]=="recess": continue
                vertices,faces = primitive_mesh(primitive)
                obj = mesh_object(primitive["id"],vertices,faces,self.collections["Anatomy"],self.material)
                obj.parent=carrier;obj.matrix_parent_inverse=Matrix.Identity(4)
                obj["structure_id"]=id;obj["primitive_id"]=primitive["id"];obj["rigid"]=body["rigid"]
                self.meshes[primitive["id"]] = obj
            for primitive in body["geometry"]:
                if primitive["type"]!="recess": continue
                vertices,faces=primitive_mesh(primitive)
                cutter=mesh_object(primitive["id"],vertices,faces,self.collections["Anatomy"])
                cutter.parent=carrier;cutter.matrix_parent_inverse=Matrix.Identity(4)
                target=self.meshes[primitive["target"]]
                modifier=target.modifiers.new(primitive["id"],'BOOLEAN')
                modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
                # Boolean recesses are construction-time geometry. Re-solving
                # them after every rigid pose can change floating-point topology.
                bpy.context.view_layer.objects.active=target
                target.select_set(True)
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                target.select_set(False)
                bpy.data.objects.remove(cutter,do_unlink=True)
        mapping = prepared["sources"]["humanoid-map"]
        for entry in mapping["entries"]:
            obj=bpy.data.objects.new("humanoid."+entry["humanoid"],None)
            self.collections["Humanoid"].objects.link(obj)
            obj["humanoid_bone"]=entry["humanoid"];obj["structure_id"]=entry["target"]
            constraint=obj.constraints.new('COPY_TRANSFORMS');constraint.target=self.rig;constraint.subtarget=entry["target"]
            self.semantic[entry["humanoid"]]=obj
        self.make_scene()
        self.reference_local = None
        self.review_markers={}

    def make_rig(self):
        data=bpy.data.armatures.new("AnatomicalControls")
        rig=bpy.data.objects.new("AnatomicalControls",data)
        self.collections["Controls"].objects.link(rig)
        bpy.context.view_layer.objects.active=rig;rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        rest={}
        # Reconstruct the parent-local rest transforms rather than treating neutral as rest.
        for body in self.bodies:
            q=body["rest_orientation"]
            from mathutils import Quaternion
            local=Quaternion(q).to_matrix().to_4x4();local.translation=Vector(body["rest_translation_m"])
            rest[body["id"]]=(rest[body["parent"]] @ local) if body["parent"] else local
            if body["representation"]=="omitted":continue
            bone=data.edit_bones.new(body["id"])
            if body["parent"] is not None:bone.parent=data.edit_bones[body["parent"]]
            bone.use_connect=False;bone.matrix=rest[body["id"]];bone.length=.025*self.height
            bone.inherit_scale='NONE'
        bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
        for bone in rig.pose.bones:
            bone.rotation_mode='QUATERNION';bone.scale=(1,1,1)
            target=bpy.data.objects.new('target.'+bone.name,None)
            self.collections['Controls'].objects.link(target)
            target.parent=self.world_root;target.rotation_mode='QUATERNION'
            target.matrix_basis=rest[bone.name]
            target.scale=(1,1,1);target.rotation_quaternion.normalize()
            constraint=bone.constraints.new('COPY_TRANSFORMS')
            constraint.target=target;constraint.owner_space='WORLD';constraint.target_space='WORLD'
            self.targets[bone.name]=target
        return rig

    def make_scene(self):
        scene=bpy.context.scene;source=self.scene_source;shading=source["shading"]
        scene.render.engine=source["backend"]["renderer"]
        scene.render.resolution_x,scene.render.resolution_y=source["resolution"]
        scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
        scene.render.film_transparent=shading["transparent"]
        display=scene.display.shading
        display.light=shading["light"];display.color_type=shading["color_type"]
        display.background_type='WORLD';scene.world.color=shading["background"]
        display.show_object_outline=shading["outlines"];display.object_outline_color=shading["outline_color"]
        display.show_shadows=shading["shadows"];display.show_cavity=shading["cavity"];display.show_xray=False
        scene.display.render_aa=str(shading["antialiasing"])
        scene.view_settings.view_transform='Standard'
        scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
        half=source["floor"]["size_m"]/2;z=source["floor"]["z_m"]
        floor_material=bpy.data.materials.new('fixed-floor');floor_material.diffuse_color=(*source["floor"]["color"],1)
        self.floor=mesh_object('Floor',[(-half,-half,z),(half,-half,z),(half,half,z),(-half,half,z)],[(0,1,2),(0,2,3)],self.collections["Review"],floor_material)
        self.cameras={}
        for definition in source["cameras"]:
            data=bpy.data.cameras.new('camera.'+definition["id"]);data.type='ORTHO';data.ortho_scale=definition["orthographic_scale_m"]
            camera=bpy.data.objects.new('camera.'+definition["id"],data);self.collections["Review"].objects.link(camera)
            camera.location=definition["position_m"]
            camera.rotation_euler=(Vector(definition["look_at_m"])-camera.location).to_track_quat('-Z','Y').to_euler()
            self.cameras[definition["id"]]=camera
        scene.camera=self.cameras['front']

    def apply_sample(self,sample):
        from mathutils import Quaternion
        root=sample['world_root']
        root_matrix=Quaternion(root['orientation']).to_matrix().to_4x4()
        root_matrix.translation=Vector(root['translation_m'])
        self.world_root.matrix_world=root_matrix
        for body in self.bodies:
            id=body["id"]
            if id not in self.rig.pose.bones:continue
            pose=self.rig.pose.bones[id];rest=self.rig.data.bones[id].matrix_local
            target=root_matrix.inverted() @ matrix(sample["frames"][id])
            if pose.parent:
                parent_rest=pose.parent.bone.matrix_local
                rest=parent_rest.inverted() @ rest
                target=matrix(sample["frames"][body["parent"]]).inverted() @ matrix(sample["frames"][id])
            pose.matrix_basis=rest.inverted() @ target
            # Decomposing a float32 matrix can introduce tiny local scale and
            # quaternion errors; allowing those to multiply along the spinal
            # chain violates the rigid-frame contract. Only rigid channels exist.
            pose.scale=(1,1,1)
            pose.rotation_quaternion.normalize()
            # Preserve the anatomical bone hierarchy while pinning its evaluated
            # frame to the authoritative data-side solution. A world-space
            # adapter avoids cumulative float32 translation cancellation along
            # the 24-vertebra chain. These are computed targets, not extra DOFs.
            adapter=self.targets[id]
            adapter.matrix_basis=root_matrix.inverted() @ matrix(sample['frames'][id])
            adapter.scale=(1,1,1);adapter.rotation_quaternion.normalize()
        for name,points in sample["guides"].items():
            body=self.index[self.meshes[name]["structure_id"]]
            primitive=next(g for g in body["geometry"] if g["id"]==name)
            vertices,faces=primitive_mesh(primitive,points)
            mesh=self.meshes[name].data
            if len(vertices)!=len(mesh.vertices):raise ValueError("Guide topology changed")
            for vertex,position in zip(mesh.vertices,vertices):vertex.co=position
            mesh.update()
        bpy.context.view_layer.update()

    def balance_evidence(self):
        """Cheap actual-bone/attachment evidence also retained by render-only runs."""
        depsgraph=bpy.context.evaluated_depsgraph_get();rig=self.rig.evaluated_get(depsgraph)
        frames={id:frame(rig.matrix_world @ rig.pose.bones[id].matrix) for id in sorted(self.carriers)}
        points={r['id']:{'structure':r['body'],'position_m':list(rig.matrix_world @ rig.pose.bones[r['body']].matrix @ Vector(r['position_m']))}
                for r in self.profile['mass_model']['segments']}
        support={}
        for body in self.bodies:
            if body['id'] not in self.carriers:continue
            world=self.carriers[body['id']].evaluated_get(depsgraph).matrix_world
            for a in body['attachments']:
                if a['id'].startswith('contact.'):
                    support[a['id']]={'structure':body['id'],'position_m':list(world @ Vector(a['position_m']))}
        return {'frames':frames,'mass_points':points,'attachments':support}

    def measure(self,sample):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        rig=self.rig.evaluated_get(depsgraph)
        frames={id:frame(rig.matrix_world @ rig.pose.bones[id].matrix) for id in sorted(self.carriers)}
        geometry={}
        for name,obj in sorted(self.meshes.items()):
            evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
            local=[list(v.co) for v in mesh.vertices]
            world=[evaluated.matrix_world @ v.co for v in mesh.vertices]
            topology={"vertices":len(mesh.vertices),"triangles":[list(p.vertices) for p in mesh.polygons]}
            entry={"structure":obj["structure_id"],"rigid":bool(obj["rigid"]),"scale":list(evaluated.scale),
                   "vertex_count":len(mesh.vertices),"topology_sha256":hashlib.sha256(json.dumps(topology,sort_keys=True).encode()).hexdigest(),
                   "local_bounds_m":[[min(v[i] for v in local) for i in range(3)],[max(v[i] for v in local) for i in range(3)]],
                   "world_bounds_m":[[min(v[i] for v in world) for i in range(3)],[max(v[i] for v in world) for i in range(3)]],
                   "world_matrix":[list(row) for row in evaluated.matrix_world]}
            if self.reference_local is not None and entry["rigid"]:
                previous=self.reference_local[name]
                entry["rigid_vertex_residual_m"]=max((Vector(a)-Vector(b)).length for a,b in zip(local,previous)) if len(local)==len(previous) else float('inf')
            else:entry["rigid_vertex_residual_m"]=0.
            if name.startswith(('rib.', 'cartilage.')):
                count=len(self.primitive_index[name]['points_m'])
                # Tube ring means recover the actual evaluated centerline,
                # independently of the prepared guide controls.
                if count in (3,5) and len(world)==17*16:
                    entry['controls_m']=[list(sum((world[k] for k in range(ring*16,(ring+1)*16)),Vector())/16)
                                         for ring in [i*16//(count-1) for i in range(count)]]
            elif name=='sternum.geometry.0' and self.primitive_index[name]['type']=='shell':
                count=len(world)//2
                entry['controls_m']=[list((world[i]+world[i+count])/2) for i in range(count)]
                entry['thicknesses_m']=[(world[i]-world[i+count]).length for i in range(count)]
            geometry[name]=entry;evaluated.to_mesh_clear()
        if self.reference_local is None:
            self.reference_local={}
            for name,obj in sorted(self.meshes.items()):
                evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
                self.reference_local[name]=[list(v.co) for v in mesh.vertices];evaluated.to_mesh_clear()
        attachments={}
        landmarks={}
        for body in self.bodies:
            id=body["id"]
            if id not in self.carriers:continue
            carrier=self.carriers[id].evaluated_get(depsgraph);world=carrier.matrix_world
            for attachment in body["attachments"]:
                attachments[attachment["id"]]={"structure":id,"position_m":list(world @ Vector(attachment["position_m"])),"local_position_m":attachment["position_m"]}
        # Frozen neutral landmarks are converted into body-local positions once.
        for landmark in self.profile["landmarks"]:
            body_id = landmark.get("attachment_body")
            if body_id is None:
                landmarks[landmark["id"]]={"structure":None,"position_m":landmark["position_m"]}
                continue
            if body_id not in self.carriers:
                landmarks[landmark["id"]]={"structure":body_id,"status":"omitted"}
                continue
            if landmark["frame"]!='world':
                local=Vector(landmark["position_m"])
            else:
                body=self.index[body_id]
                neutral=matrix({"position_m":body["origin_m"],"rotation":body["basis"]})
                local=neutral.inverted() @ Vector(landmark["position_m"])
            if body_id in self.carriers:landmarks[landmark["id"]]={"structure":body_id,"position_m":list(self.carriers[body_id].evaluated_get(depsgraph).matrix_world @ local)}
        mass_points={r['id']:{'structure':r['body'], 'position_m':list(rig.matrix_world @ rig.pose.bones[r['body']].matrix @ Vector(r['position_m']))}
                     for r in self.profile['mass_model']['segments']}
        return {"id":sample["id"],"frames":frames,"geometry":geometry,"attachments":attachments,"landmarks":landmarks,'mass_points':mass_points,
                'world_root':frame(self.world_root.evaluated_get(depsgraph).matrix_world),
                "object_scales":{id:list(obj.evaluated_get(depsgraph).matrix_world.to_scale()) for id,obj in sorted(self.carriers.items())},
                "bone_scales":{bone.name:list(bone.scale) for bone in rig.pose.bones},"scene":self.scene_measurements()}

    def scene_measurements(self):
        scene=bpy.context.scene;display=scene.display.shading
        return {"cameras":{id:{"matrix_world":[list(row) for row in camera.matrix_world],"ortho_scale_m":camera.data.ortho_scale,"type":camera.data.type} for id,camera in sorted(self.cameras.items())},
                "floor_matrix":[list(row) for row in self.floor.matrix_world],"floor_vertices":[list(v.co) for v in self.floor.data.vertices],
                "floor_color":list(self.floor.data.materials[0].diffuse_color),"bone_color":list(self.material.diffuse_color),
                "lights":[obj.name for obj in bpy.data.objects if obj.type=='LIGHT'],"renderer":scene.render.engine,
                "resolution":[scene.render.resolution_x,scene.render.resolution_y],"resolution_percentage":scene.render.resolution_percentage,
                "light":display.light,"color_type":display.color_type,"background":list(scene.world.color),
                "outlines":display.show_object_outline,"outline_color":list(display.object_outline_color),
                "shadows":display.show_shadows,"cavity":display.show_cavity,"transparent":scene.render.film_transparent,"antialiasing":scene.display.render_aa}

    def metadata(self):
        import gpu
        gpu.init()
        from pathlib import Path
        root=Path(__file__).resolve().parent.parent
        visibility={}
        for name,collection in self.collections.items():
            baseline={id:other.hide_render for id,other in self.collections.items()}
            collection.hide_render=not baseline[name]
            visibility[name]=all(other.hide_render==baseline[id] for id,other in self.collections.items() if id!=name)
            collection.hide_render=baseline[name]
        return {"blender_version":bpy.app.version_string,"blender_build":bpy.app.build_hash.decode(),
                "platform":platform.system()+'-'+platform.machine(),"mpfb":"not-used","rigify":"not-used",
                "gpu":{"vendor":gpu.platform.vendor_get(),"renderer":gpu.platform.renderer_get(),"version":gpu.platform.version_get()},
                "collections":sorted(self.collections),"native_bones":sorted(b.name for b in self.rig.data.bones),
                'independent_collection_visibility':visibility,
                'implementation_hashes':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((root/'tools').glob('*.py'))},
                "semantic_targets":{name:obj["structure_id"] for name,obj in sorted(self.semantic.items())}}

    def render(self,sample,directory):
        from pathlib import Path
        # These are review annotations, excluded from skeletal geometry metrics.
        if not self.review_markers:
            self.marker_material=bpy.data.materials.new('declared-contact');self.marker_material.diffuse_color=(.05,.5,.1,1)
            for side in ('L','R'):
                for name in ('heel','medial_ball','lateral_ball'):
                    id=f'contact.{name}.{side}'
                    vertices,faces=primitive_mesh({'type':'sphere','center_m':[0,0,0],'radius_m':.004*self.height})
                    obj=mesh_object('review.'+id,vertices,faces,self.collections['Review'],self.marker_material)
                    self.review_markers[id]=obj
            line_material=bpy.data.materials.new('floor-reference-line');line_material.diffuse_color=(.12,.12,.12,1)
            for axis in (0,1):
                start,end=[0.,0.,0.],[0.,0.,0.];start[axis]=-3;end[axis]=3
                vertices,faces=primitive_mesh({'type':'tube','points_m':[start,end],'radius_m':.0008*self.height})
                mesh_object('review.floor_axis.'+str(axis),vertices,faces,self.collections['Review'],line_material)
        for obj in self.review_markers.values():obj.hide_render=True
        for contact in sample['contacts']:
            for id,target in zip(contact['anchors'],contact['targets_m']):
                if id in self.review_markers:
                    obj=self.review_markers[id];obj.hide_render=False;obj.location=target
        bpy.context.view_layer.update()
        result={}
        views=('front','rear','side') if sample['fixture'] in ('neutral','rest') else ('front','side')
        for view in views:
            path=Path(directory)/sample['fixture']/view/(str(sample['frame_id']).zfill(5)+'.png')
            path.parent.mkdir(parents=True,exist_ok=True)
            bpy.context.scene.camera=self.cameras[view]
            bpy.context.scene.render.filepath=str(path.resolve())
            bpy.ops.render.render(write_still=True)
            result[view]=str(path.relative_to(directory))
        if sample['fixture'] in ('neutral','rest'):
            visible={name:obj.hide_render for name,obj in self.meshes.items()}
            for view in sorted(name for name in self.cameras if name.startswith('thorax-')):
                for isolated in (False,True):
                    key=view+('-isolated' if isolated else '')
                    for name,obj in self.meshes.items():
                        body=obj['structure_id']
                        include=body.startswith(('rib.','cartilage.','clavicle.')) or body=='sternum' or (body[0] in 'CTL' and body[1:].isdigit())
                        obj.hide_render=visible[name] or (isolated and not include)
                    path=Path(directory)/sample['fixture']/key/(str(sample['frame_id']).zfill(5)+'.png')
                    path.parent.mkdir(parents=True,exist_ok=True)
                    bpy.context.scene.camera=self.cameras[view]
                    bpy.context.scene.render.filepath=str(path.resolve())
                    bpy.ops.render.render(write_still=True)
                    result[key]=str(path.relative_to(directory))
            for name,obj in self.meshes.items():obj.hide_render=visible[name]
        return result
