# SPDX-License-Identifier: Apache-2.0
"""Headless Blender adapter; consumes prepared plain JSON only."""

import hashlib
import json
import math
import platform
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from humanmotionlib.geometry import primitive_mesh
from humanmotionlib.runtime import check_blender_version


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
    def __init__(self,prepared,characters=("skeleton",),character_request=None):
        check_blender_version(bpy.app.version_string,bpy.app.build_hash.decode())
        self.character_ids=tuple(characters)
        self.character_request=character_request or {}
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
        self.surface_collections={}
        self.surface_meshes={}
        self.surface_sources={}
        self.surface_descriptors={}
        self.surface_weight_sets={}
        self._surface_weight_set_cache={}
        self._surface_pose_cache_sample=None
        self._surface_pose_skinning_cache={}
        self.build_character_surfaces()

    def build_character_surfaces(self):
        """Build selected authored surfaces on the shared anatomical rig."""
        from humanmotionlib.character_surface import expand_surface
        from humanmotionlib.character_skinning import compile_weight_set
        for descriptor in self.character_request.get("characters",[]):
            character_id=descriptor["id"]
            surface=expand_surface(self.profile,descriptor["template"],descriptor["appearance"],self.height)
            if surface.get("surface_sha256")!=descriptor.get("surface_sha256"):
                raise ValueError("surface reconstruction digest mismatch for "+character_id)
            collection=bpy.data.collections.new("CharacterSurface."+character_id)
            bpy.context.scene.collection.children.link(collection)
            self.surface_collections[character_id]=collection
            materials={}
            for name,rgb in descriptor["appearance"]["materials_rgb"].items():
                material=bpy.data.materials.new("character."+character_id+"."+name)
                material.diffuse_color=(*rgb,1.0)
                materials[name]=material
            objects={}
            for component in surface["components"]:
                weight_key=tuple(tuple(sorted((carrier,float(weight)) for carrier,weight in row.items()))
                                 for row in component["weights"])
                compiled_key=(component["id"],weight_key)
                weight_set=self._surface_weight_set_cache.get(compiled_key)
                if weight_set is None:
                    weight_set=compile_weight_set(component["weights"])
                    self._surface_weight_set_cache[compiled_key]=weight_set
                self.surface_weight_sets[(character_id,component["id"])]=weight_set
                mesh=bpy.data.meshes.new("character."+character_id+"."+component["id"])
                mesh.from_pydata(component["vertices_m"],[],component["faces"])
                mesh.update()
                obj=bpy.data.objects.new(mesh.name,mesh)
                collection.objects.link(obj)
                # Surface vertices are authored in profile/world coordinates.
                # Keep the object under the same placement root as the rig so
                # stage/consumer root translations move undeformed vertices too;
                # the armature modifier then applies only the shared bone delta.
                obj.parent=self.world_root
                obj.matrix_parent_inverse=Matrix.Identity(4)
                obj["character_id"]=character_id
                obj["component_id"]=component["id"]
                for name,material in materials.items():mesh.materials.append(material)
                material_slots={name:index for index,name in enumerate(component.get("material_ids",materials))}
                for face,material_name in zip(mesh.polygons,component.get("face_materials",())):
                    face.material_index=material_slots.get(material_name,0)
                    face.use_smooth=True
                weight_names=sorted({bone for row in component["weights"] for bone in row})
                groups={name:obj.vertex_groups.new(name=name) for name in weight_names}
                for index,row in enumerate(component["weights"]):
                    for bone,weight in row.items():
                        if weight>0.0:groups[bone].add([index],float(weight),'REPLACE')
                modifier=obj.modifiers.new("SharedAnatomicalRig",'ARMATURE')
                modifier.object=self.rig
                modifier.use_deform_preserve_volume=True
                modifier.use_vertex_groups=True
                modifier.use_bone_envelopes=False
                objects[component["id"]]=obj
            self.surface_meshes[character_id]=objects
            self.surface_sources[character_id]=surface
            self.surface_descriptors[character_id]=descriptor

    def set_character_visibility(self,character_id):
        if character_id not in self.character_ids:
            raise ValueError("unselected character: "+str(character_id))
        show_skeleton=character_id=="skeleton"
        for obj in self.meshes.values():obj.hide_render=not show_skeleton
        for identifier,collection in self.surface_collections.items():
            for obj in collection.objects:obj.hide_render=(identifier!=character_id)

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
            # Blender's edit-bone matrix setter re-aligns the longitudinal
            # local-Y axis when length is assigned.  Set endpoints from the
            # canonical HML frame directly, then align roll to its local-Z
            # axis so stored Bone.matrix_local remains the shared rest frame.
            desired=rest[body["id"]]
            desired_basis=desired.to_3x3()
            head=desired.translation.copy()
            axis_y=(desired_basis @ Vector((0,1,0))).normalized()
            axis_z=(desired_basis @ Vector((0,0,1))).normalized()
            bone.use_connect=False
            bone.head=head
            bone.tail=head+axis_y*(.025*self.height)
            bone.align_roll(axis_z)
            bone.inherit_scale='NONE'
        # Keep the authored armature-space rest frames for native diagnostics.
        self.rest_matrices = rest
        bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
        if self.character_request.get('characters'):
            matrix_audit={}
            worst=(0.0,None)
            for body in self.bodies:
                identifier=body['id']
                if identifier not in rig.data.bones:continue
                canonical=rest[identifier]
                actual=rig.data.bones[identifier].matrix_local
                difference=max(abs(float(actual[row][column]-canonical[row][column]))
                               for row in range(4) for column in range(4))
                translation_difference=math.dist(
                    tuple(float(actual[row][3]) for row in range(3)),
                    tuple(float(canonical[row][3]) for row in range(3)))
                rotation_difference=max(abs(float(actual[row][column]-canonical[row][column]))
                                        for row in range(3) for column in range(3))
                matrix_audit[identifier]={
                    'maximum_absolute_difference':difference,
                    'translation_difference_m':translation_difference,
                    'rotation_basis_maximum_absolute_difference':rotation_difference,
                    'canonical_rest_matrix':[[float(canonical[row][column]) for column in range(4)] for row in range(4)],
                    'data_bone_matrix_local':[[float(actual[row][column]) for column in range(4)] for row in range(4)],
                }
                if difference>worst[0]:worst=(difference,identifier)
            print('HML_CANONICAL_REST_MATRIX_AUDIT '+json.dumps({
                'tolerance_m':1e-5*self.height,'worst_absolute_difference':worst[0],
                'worst_structure_id':worst[1],'bones':matrix_audit,
            },sort_keys=True),flush=True)
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
        self._surface_pose_cache_sample=sample
        self._surface_pose_skinning_cache={}
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

    def _evaluated_surface_vertices(self,obj):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        evaluated=obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh()
        try:
            if len(mesh.vertices)!=len(obj.data.vertices):
                raise ValueError('surface topology changed under deformation: '+obj.name)
            local=[list(vertex.co) for vertex in mesh.vertices]
            world=[list(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
            return local,world
        finally:evaluated.to_mesh_clear()

    def _compiled_surface_pose(self,space,transforms,weight_set):
        """Reuse reference blends only within the currently applied source sample."""
        from humanmotionlib.character_skinning import compile_pose_skinning
        cache=self._surface_pose_skinning_cache
        # Weight sets are immutable and retained by this backend. Use identity
        # here so cache lookup does not repeatedly hash every vertex index.
        key=(space,id(weight_set))
        compiled=cache.get(key)
        if compiled is None:
            compiled=compile_pose_skinning(transforms,weight_set)
            cache[key]=compiled
        return compiled

    def surface_reference_record(self,character_id,prepared_sha256,render_identity):
        surface=self.surface_sources[character_id]
        rows=[];tolerance=1e-5*self.height
        for component in surface['components']:
            obj=self.surface_meshes[character_id][component['id']]
            _,native=self._evaluated_surface_vertices(obj)
            residuals=[math.dist(expected,actual) for expected,actual in zip(component['vertices_m'],native)]
            maximum=max(residuals,default=0.0)
            worst=residuals.index(maximum) if residuals else None
            if maximum>tolerance:
                index=worst if worst is not None else 0
                vertex=component['vertices_m'][index]
                carriers=sorted(component['weights'][index])
                depsgraph=bpy.context.evaluated_depsgraph_get()
                evaluated_obj=obj.evaluated_get(depsgraph)
                native_vertex=native[index]
                def rows(value):return [[float(value[row][column]) for column in range(4)] for row in range(4)]
                carrier_debug={}
                for carrier in carriers:
                    data_bone=self.rig.data.bones[carrier]
                    pose_bone=self.rig.pose.bones[carrier]
                    target=self.targets[carrier]
                    carrier_debug[carrier]={
                        'weight':component['weights'][index][carrier],
                        'canonical_rest_matrix':rows(self.rest_matrices[carrier]),
                        'data_bone_matrix_local':rows(data_bone.matrix_local),
                        'pose_bone_matrix':rows(pose_bone.matrix),
                        'pose_minus_rest':rows(pose_bone.matrix @ data_bone.matrix_local.inverted()),
                        'target_matrix_world':rows(target.matrix_world),
                        'parent':data_bone.parent.name if data_bone.parent else None,
                    }
                diagnostic={
                    'character_id':character_id,'component_id':component['id'],
                    'vertex_id':component['vertex_ids'][index],
                    'rest_vertex_m':vertex,'native_vertex_m':native_vertex,
                    'residual_m':maximum,'weights':component['weights'][index],
                    'rig_matrix_world':rows(self.rig.matrix_world),
                    'mesh_matrix_world':rows(obj.matrix_world),
                    'evaluated_mesh_matrix_world':rows(evaluated_obj.matrix_world),
                    'world_root_matrix_world':rows(self.world_root.matrix_world),
                    'carriers':carrier_debug,
                }
                print('HML_NATIVE_REST_DIAGNOSTIC '+json.dumps(diagnostic,sort_keys=True),flush=True)
                raise ValueError(f"native rest surface residual exceeds tolerance: {character_id}/{component['id']} vertex={component['vertex_ids'][index]} residual_m={maximum}")
            rows.append({key:component[key] for key in ('id','material','material_ids','face_materials','vertices_m','vertex_ids','faces','weights')} | {
                'native_rest_vertices_m':native,'maximum_rest_residual_m':maximum,
                'worst_rest_vertex_id':component['vertex_ids'][worst] if worst is not None else None})
        return {'format':'hml-surface-reference/v1','prepared_sha256':prepared_sha256,
                'render_identity':render_identity,'character_id':character_id,
                'profile_id':self.profile['id'],'surface_sha256':surface['surface_sha256'],
                'template_id':self.surface_descriptors[character_id]['definition']['template_id'],
                'appearance_id':self.surface_descriptors[character_id]['definition']['appearance_id'],
                'stature_m':self.height,'components':rows}

    def measure_surface(self,character_id,sample):
        from humanmotionlib.character_skinning import skin_vertex,source_world_transforms
        from humanmotionlib.character_surface import _rest_frames
        if self._surface_pose_cache_sample is not sample:
            self._surface_pose_cache_sample=sample
            self._surface_pose_skinning_cache={}
        if not hasattr(self,'canonical_surface_rest_frames'):
            _,self.canonical_surface_rest_frames=_rest_frames(self.profile,1.0)
        bone_names=sorted({bone for component in self.surface_sources[character_id]['components']
                           for row in component['weights'] for bone in row})
        depsgraph=bpy.context.evaluated_depsgraph_get()
        rig=self.rig.evaluated_get(depsgraph)
        native_local_transforms={}
        canonical_world_transforms=source_world_transforms(
            self.profile,sample['frames'],bone_names,rest_frames=self.canonical_surface_rest_frames)
        for bone_name in bone_names:
            local_rest=self.rig.data.bones[bone_name].matrix_local
            local_pose=rig.pose.bones[bone_name].matrix
            local_rest_translation,local_rest_rotation,_=local_rest.decompose()
            local_pose_translation,local_pose_rotation,_=local_pose.decompose()
            native_local_transforms[bone_name]={
                'rest_translation':tuple(local_rest_translation),'rest_orientation':tuple(local_rest_rotation),
                'posed_translation':tuple(local_pose_translation),'posed_orientation':tuple(local_pose_rotation)}

            source_frame=sample['frames'][bone_name]
            source_pose=matrix(source_frame)

            observed_world=rig.matrix_world @ local_pose
            placement_translation_error=(observed_world.translation-source_pose.translation).length
            placement_rotation_error=max(abs(float(observed_world[row][column]-source_pose[row][column]))
                                         for row in range(3) for column in range(3))
            if placement_translation_error>1e-5*self.height or placement_rotation_error>1e-5:
                raise ValueError(f"native/source bone placement mismatch: {character_id}/{sample['id']}/{bone_name} "
                                 f"translation_residual_m={placement_translation_error} "
                                 f"rotation_basis_residual={placement_rotation_error}")
        components=[];foot_triangles={}
        floor_min=float('inf');floor_vertex=None
        for component_id,obj in sorted(self.surface_meshes[character_id].items()):
            local_vertices,vertices=self._evaluated_surface_vertices(obj)
            ids=self.surface_sources[character_id]['components']
            component=next(row for row in ids if row['id']==component_id)
            weight_set=self.surface_weight_sets[(character_id,component_id)]
            local_kernel=self._compiled_surface_pose('native-local',native_local_transforms,weight_set)
            world_kernel=self._compiled_surface_pose('source-world',canonical_world_transforms,weight_set)
            local_residuals=[]
            world_residuals=[]
            for index,(rest_vertex,weights,native_local,native_world) in enumerate(zip(
                    component['vertices_m'],component['weights'],local_vertices,vertices)):
                local_reference=local_kernel.apply(rest_vertex,index)
                world_reference=world_kernel.apply(rest_vertex,index)
                local_residuals.append(math.dist(local_reference,native_local))
                world_residuals.append(math.dist(world_reference,native_world))
            maximum_residual=max(world_residuals,default=0.0)
            worst_index=world_residuals.index(maximum_residual) if world_residuals else None
            local_max=max(local_residuals,default=0.0)
            world_max=max(world_residuals,default=0.0)
            local_worst_index=local_residuals.index(local_max) if local_residuals else None
            if max(local_max,world_max)>1e-5*self.height:
                index=(local_worst_index if local_max>world_max else worst_index)
                vertex_id=component['vertex_ids'][index] if index is not None else 'unknown'
                local_vertex=local_residuals[index] if index is not None else 0.0
                world_vertex=world_residuals[index] if index is not None else 0.0
                carriers=sorted(component['weights'][index])
                def matrix_rows(value):
                    return [[float(value[row][column]) for column in range(4)] for row in range(4)]
                diagnostic={
                    'character_id':character_id,'sample_id':sample['id'],
                    'component_id':component_id,'vertex_id':vertex_id,
                    'rest_vertex_m':component['vertices_m'][index],
                    'weights':component['weights'][index],
                    'native_local_vertex_m':local_vertices[index],
                    'native_world_vertex_m':vertices[index],
                    'native_local_reference_m':skin_vertex(
                        component['vertices_m'][index],component['weights'][index],native_local_transforms),
                    'source_world_reference_m':skin_vertex(
                        component['vertices_m'][index],component['weights'][index],canonical_world_transforms),
                    'world_root_matrix_world':matrix_rows(self.world_root.matrix_world),
                    'rig_matrix_world':matrix_rows(rig.matrix_world),
                    'mesh_matrix_world':matrix_rows(obj.matrix_world),
                    'carrier_matrices':{
                        carrier:{'canonical_rest':matrix_rows(self.rest_matrices[carrier]),
                                 'blender_rest_local':matrix_rows(self.rig.data.bones[carrier].matrix_local),
                                 'blender_pose_local':matrix_rows(rig.pose.bones[carrier].matrix)}
                        for carrier in carriers},
                }
                print('HML_NATIVE_SKIN_DIAGNOSTIC '+json.dumps(diagnostic,sort_keys=True),flush=True)
                raise ValueError(f"native/reference skinning mismatch: {character_id}/{sample['id']}/{component_id} "
                                 f"vertex={vertex_id} local_residual_m={local_vertex} "
                                 f"source_world_residual_m={world_vertex} bound_m={1e-5*self.height}")
            local_min=min((vertex[2],index) for index,vertex in enumerate(vertices))
            if local_min[0]<floor_min:floor_min,floor_vertex=local_min[0],component['vertex_ids'][local_min[1]]
            if component_id.startswith('foot.'):
                foot_triangles[component_id]=(vertices,component['faces'])
            components.append({'id':component_id,'vertex_ids':component['vertex_ids'],
                               'vertices_m':vertices,'minimum_z_m':local_min[0],
                               'worst_floor_vertex_id':component['vertex_ids'][local_min[1]],
                               'maximum_reference_residual_m':maximum_residual,
                               'maximum_native_local_residual_m':local_max,
                               'maximum_source_world_residual_m':world_max,
                               'worst_reference_vertex_id':component['vertex_ids'][worst_index] if worst_index is not None else None,
                               'worst_native_local_vertex_id':component['vertex_ids'][local_worst_index] if local_worst_index is not None else None})
        floor_limit=-1e-4*self.height
        if floor_min<floor_limit:
            raise ValueError(f"surface floor penetration: {character_id}/{sample['id']} minimum_z_m={floor_min} vertex={floor_vertex}")
        contacts=[]
        attachment_map={attachment['id']:(body['id'],attachment['position_m'])
                        for body in self.bodies for attachment in body.get('attachments',[])}
        for contact in sample.get('contacts',[]):
            for anchor_id,target in zip(contact.get('anchors',[]),contact.get('targets_m',[])):
                side='L' if str(anchor_id).endswith('.L') else 'R'
                foot=foot_triangles.get('foot.'+side)
                if not foot:continue
                if anchor_id not in attachment_map:raise ValueError('unknown surface contact attachment '+str(anchor_id))
                carrier,local=attachment_map[anchor_id]
                if carrier not in rig.pose.bones:raise ValueError('contact carrier is missing from evaluated rig '+carrier)
                posed_frame=rig.matrix_world @ rig.pose.bones[carrier].matrix
                anchor=list(posed_frame @ Vector(local))
                distance,closest_id=self._closest_foot_distance(anchor,*foot)
                contacts.append({'anchor_id':anchor_id,'anchor_m':anchor,'target_m':target,
                                 'closest_sole_distance_m':distance,'closest_sole_triangle_id':closest_id})
        return {'sample_id':sample['id'],'fixture':sample['fixture'],'beat':sample['beat'],
                'components':components,'minimum_z_m':floor_min,'worst_floor_vertex_id':floor_vertex,
                'contacts':contacts}

    @staticmethod
    def _closest_foot_distance(point,vertices,faces):
        p=Vector(point);best=float('inf');best_index=None
        for index,face in enumerate(faces):
            if len(face)!=3:continue
            a,b,c=(Vector(vertices[i]) for i in face)
            ab=b-a;ac=c-a;ap=p-a;d1=ab.dot(ap);d2=ac.dot(ap)
            if d1<=0 and d2<=0:q=a
            else:
                bp=p-b;d3=ab.dot(bp);d4=ac.dot(bp)
                if d3>=0 and d4<=d3:q=b
                else:
                    vc=d1*d4-d3*d2
                    if vc<=0 and d1>=0 and d3<=0:q=a+ab*(d1/(d1-d3))
                    else:
                        cp=p-c;d5=ab.dot(cp);d6=ac.dot(cp)
                        if d6>=0 and d5<=d6:q=c
                        else:
                            vb=d5*d2-d1*d6
                            if vb<=0 and d2>=0 and d6<=0:q=a+ac*(d2/(d2-d6))
                            else:
                                va=d3*d6-d5*d4
                                if va<=0 and d4-d3>=0 and d5-d6>=0:q=b+(c-b)*((d4-d3)/((d4-d3)+(d5-d6)))
                                else:
                                    denom=1.0/(va+vb+vc);v=vb*denom;w=vc*denom;q=a+ab*v+ac*w
            distance=(p-q).length
            if distance<best:best,best_index=distance,index
        return best,best_index

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
        from humanmotionlib import __version__
        from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
        manifest=verify_runtime_integrity()
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
                'implementation_hashes':manifest['implementation'],
                'package_version':__version__,'runtime_manifest_sha256':manifest_sha256(),
                "semantic_targets":{name:obj["structure_id"] for name,obj in sorted(self.semantic.items())}}

    def render(self,sample,directory,character_id="skeleton"):
        from pathlib import Path
        self.set_character_visibility(character_id)
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
        if character_id=='skeleton':
            for contact in sample['contacts']:
                for id,target in zip(contact['anchors'],contact['targets_m']):
                    if id in self.review_markers:
                        obj=self.review_markers[id];obj.hide_render=False;obj.location=target
        bpy.context.view_layer.update()
        result={}
        views=('front','rear','side') if character_id=='skeleton' and sample['fixture'] in ('neutral','rest') else ('front','side')
        if character_id!='skeleton' and sample['fixture'] in ('neutral','rest'):
            views=('front','rear','side')
        for view in views:
            prefix=Path() if character_id=='skeleton' else Path(character_id)
            path=Path(directory)/prefix/sample['fixture']/view/(str(sample['frame_id']).zfill(5)+'.png')
            path.parent.mkdir(parents=True,exist_ok=True)
            bpy.context.scene.camera=self.cameras[view]
            bpy.context.scene.render.filepath=str(path.resolve())
            bpy.ops.render.render(write_still=True)
            result[view]=str(path.relative_to(directory))
        if character_id=='skeleton' and sample['fixture'] in ('neutral','rest'):
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
