const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const THREE=require('../static/core/studio/vendor/three-r128.min.js');
const context={window:{},THREE};
const source=fs.readFileSync('core/static/core/studio/engine.js','utf8');
vm.runInNewContext(source.replace('return{create};','return{create,batchStatic};'),context);
const {batchStatic}=context.window.RvionStudioEngine;
test('immutable box batching preserves world geometry, materials, layers and shadows',()=>{
 const root=new THREE.Group(),parent=new THREE.Group(),material=new THREE.MeshStandardMaterial();
 root.position.set(50,2,-14);root.rotation.y=.4;parent.position.set(3,0,-2);parent.rotation.z=.2;root.add(parent);
 const boxes=[[1,2,3],[2,1,4],[.5,.2,1]].map((size,i)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...size),material);m.position.set(i,2*i,-i);m.rotation.y=i*.3;m.castShadow=m.receiveShadow=true;m.layers.set(2);parent.add(m);return m;});
 root.updateMatrixWorld(true);
 const originals=boxes.map(m=>{const p=m.geometry.parameters;return m.matrixWorld.clone().multiply(new THREE.Matrix4().makeScale(p.width,p.height,p.depth));});
 assert.equal(batchStatic(root),2);
 const batch=root.children.find(m=>m.isInstancedMesh);
 assert.equal(batch.material,material);assert.equal(batch.count,3);assert.ok(batch.castShadow&&batch.receiveShadow);assert.equal(batch.layers.mask,4);
 root.updateMatrixWorld(true);
 originals.forEach((expected,i)=>{const actual=new THREE.Matrix4();batch.getMatrixAt(i,actual);actual.premultiply(batch.matrixWorld);actual.elements.forEach((n,k)=>assert.ok(Math.abs(n-expected.elements[k])<1e-5));});
});
test('moving subtrees, transparent surfaces and existing instances are not flattened',()=>{
 const root=new THREE.Group(),moving=new THREE.Group(),opaque=new THREE.MeshBasicMaterial(),glass=new THREE.MeshBasicMaterial({transparent:true});root.add(moving);
 const a=new THREE.Mesh(new THREE.BoxGeometry(),opaque),b=a.clone();moving.add(a,b);
 const transparent=new THREE.Mesh(new THREE.BoxGeometry(),glass);root.add(transparent,transparent.clone());
 const instanced=new THREE.InstancedMesh(new THREE.BoxGeometry(),opaque,2);root.add(instanced);
 assert.equal(batchStatic(root,[moving]),0);assert.equal(a.parent,moving);assert.equal(b.parent,moving);assert.equal(instanced.parent,root);assert.equal(transparent.parent,root);
 moving.position.x=3;root.updateMatrixWorld(true);assert.equal(a.matrixWorld.elements[12],3);
});
test('mesh parents retaining visible children are never removed',()=>{
 const root=new THREE.Group(),material=new THREE.MeshBasicMaterial();
 const parent=new THREE.Mesh(new THREE.BoxGeometry(),material);parent.add(new THREE.Mesh(new THREE.PlaneGeometry(),material));root.add(parent,parent.clone());
 batchStatic(root);assert.equal(parent.parent,root);assert.equal(root.children.find(m=>m.isInstancedMesh).count,2);
});
