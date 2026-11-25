# check_gs.py
import genesis as gs
gs.init(backend=gs.amdgpu)
print(gs.backend)

scene = gs.Scene(show_viewer=False)
scene.add_entity(gs.morphs.Plane())
scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
scene.build()
for _ in range(100):
    scene.step()
print("OK")
