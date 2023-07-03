from math import pi, atan
import pandas as pd
import random
import time
import cv2
import numpy as np

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import Point3, PointLight, Texture, CardMaker
import simplepbr

import pyautogui as pag
from panda3d.core import loadPrcFileData

from BlazeposeDepthaiEdge import BlazeposeDepthai
tracker = BlazeposeDepthai(
    input_src="rgb", pd_model=None, lm_model=None, smoothing=False, xyz=True, crop=None, internal_fps=None,
    internal_frame_height=640, force_detection=None, stats=True, trace=None
)

df = pd.read_csv("sakura_pos.csv")

#loadPrcFileData('', 'win-size 2160 3780'.format(pag.size()[0], pag.size()[1])) 
loadPrcFileData('', 'win-size 1080 1890'.format(pag.size()[0], pag.size()[1])) 
print(pag.size())

rgb = {"right":(0,1,0), "left":(1,0,0), "middle":(1,1,0)}
LINES_BODY = [[9,10],[4,6],[1,3],
            [12,14],[14,16],[16,20],[20,18],[18,16],
            [12,11],[11,23],[23,24],[24,12],
            [11,13],[13,15],[15,19],[19,17],[17,15],
            [24,26],[26,28],[32,30],
            [23,25],[25,27],[29,31]]
COLORS_BODY = ["middle","right","left",
                "right","right","right","right","right",
                "middle","middle","middle","middle",
                "left","left","left","left","left",
                "right","right","right","left","left","left"]
COLORS_BODY = [rgb[x] for x in COLORS_BODY]

class MyApp(ShowBase):
    S = 1
    fore_foot = 0 # 0：右、1：左
    nb_kps = 33
    presence_threshold = 0.5
    def __init__(self):

        ShowBase.__init__(self)
        simplepbr.init()

        # Disable the camera trackball controls.
        self.disableMouse()

        camPX, camPY, camPZ = 0, -30, 2
        self.camera.setPos(camPX, camPY, camPZ)
        camHY = -atan(camPZ/camPY)/pi*180
        print(camHY)
        self.camera.setHpr(0, camHY, 0)

        pliPX, pliPY, pliPZ = camPX, camPY - 0, camPZ + 100
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        pliPX, pliPY, pliPZ = camPX, camPY - 0, camPZ - 100
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        pliPX, pliPY, pliPZ = camPX, camPY - 100, camPZ
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        pliPX, pliPY, pliPZ = camPX, camPY + 100, camPZ
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        pliPX, pliPY, pliPZ = camPX - 100, camPY, camPZ
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        pliPX, pliPY, pliPZ = camPX + 100, camPY, camPZ
        plight = PointLight('plight')
        plight.setColor((5, 5, 5, 5))
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(pliPX, pliPY, pliPZ)
        self.render.setLight(plnp)

        self.scene = self.loader.loadModel("background.gltf")
        self.scene.setScale(1, 1, 1)
        self.scene.reparentTo(self.render)
        self.scene.setPos(0, 0, 0)
        self.scene.setHpr(180, 0, 0)

        self.tree = Actor("tree.gltf")
        self.tree.setScale(1, 1, 1)
        self.tree.reparentTo(self.render)
        self.tree.setPos(0, 0, 0)

        cm = CardMaker('card')
        self.card = self.render.attachNewNode(cm.generate())
        #self.card.setPos(-1, -25, 0.25)
        self.card.setPos(0.25, -25, 0.25)
        self.card.setShaderOff(1)
        
        self.accept('escape', self.key_esc)
        self.accept('enter', self.Step)
        
        self.taskMgr.add(self.SceneUpdateTask, "SceneUpdateTask")
        self.taskMgr.add(self.Task_GetDepthai, "Task_GetDepthai")
        self.taskMgr.add(self.Task_ImageDisplay, "Task_ImageDisplay")

    def key_esc(self):
        exit()
    
    def Step(self):
        for index, row in df[(df["S"] == self.S) & (df["M"].isna())].iterrows():
            x, y, z = row["x"], row["y"], row["z"]
            self.sakura = Actor("sakura.gltf")
            self.sakura.setScale(2, 2, 2)
            self.sakura.reparentTo(self.render)
            self.sakura.setPos(x, y, z)
            self.sakura.setHpr(random.randrange(4)*90, random.randrange(4)*90, random.randrange(4)*90)
            df.loc[index, "M"] = self.sakura
        df.loc[df["S"] == self.S, ["T"]] = time.time()
        self.S = self.S%9 + 1

    def SceneUpdateTask(self, task):
        for index, row in df[(time.time() - df["T"] > 10) & (~df["M"].isna())].iterrows():
            row["M"].delete()
            df.loc[index, "M"] = None
        return Task.cont
    
    def Task_GetDepthai(self, task):
        self.frame, self.body = tracker.next_frame()
        if self.body is not None:
            body = self.body
            th = 10
            L27, L28 = body.landmarks[27], body.landmarks[28] # 左足首、右足首
            if body.presence[27] > self.presence_threshold and body.presence[28] > self.presence_threshold:
                if L27[2] - L28[2] >= th:
                    if self.fore_foot == 1:
                        self.Step()
                    self.fore_foot = 0
                elif L27[2] - L28[2] >= -th:
                    if self.fore_foot == 0:
                        self.Step()
                    self.fore_foot = 1
        return Task.cont
    
    def Task_ImageDisplay(self, task):
        img_h, img_w, img_d = self.frame.shape

        #self.card.setScale(2, 1, 2*img_h/img_w)
        self.card.setScale(1, 1, 1*img_w/img_h)
        
        tex = Texture()
        #tex.setup2dTexture(img_w, img_h, Texture.T_unsigned_byte, Texture.FRgb)
        tex.setup2dTexture(img_h, img_w, Texture.T_unsigned_byte, Texture.FRgb)

        def is_present(body, lm_id):
            return body.presence[lm_id] > self.presence_threshold
        
        if self.body is not None:
            body = self.body
            list_connections = LINES_BODY
            lines = [np.array([body.landmarks[point,:2] for point in line]) for line in list_connections if is_present(body, line[0]) and is_present(body, line[1])]
            cv2.polylines(self.frame, lines, False, (255, 180, 90), 2, cv2.LINE_AA)

            for i,x_y in enumerate(body.landmarks[:self.nb_kps,:2]):
                if is_present(body, i):
                    if i > 10:
                        color = (0,255,0) if i%2==0 else (0,0,255)
                    elif i == 0:
                        color = (0,255,255)
                    elif i in [4,5,6,8,10]:
                        color = (0,255,0)
                    else:
                        color = (0,0,255)
                    cv2.circle(self.frame, (x_y[0], x_y[1]), 4, color, -11)

        frame = cv2.rotate(self.frame, cv2.ROTATE_180)
        #tex.setRamImage(cv2.rotate(self.frame, cv2.ROTATE_180))
        tex.setRamImage(cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE))
        self.card.setTexture(tex)
        return Task.cont


app = MyApp()
app.run()