try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as Fbui
import maya.cmds as cmds
import random
import os

ICON_PATH = "C:/Users/Cee/Documents/maya/2025/scripts/Fluffybird/ICON/icon.png"
# ✅ รูป UI ตอนเล่น และตอน Game Over
IMAGE_PATH_PLAYING = "C:/Users/Cee/Documents/maya/2025/scripts/Fluffybird/image/ui1.jpg"
IMAGE_PATH_GAMEOVER = "C:/Users/Cee/Documents/maya/2025/scripts/Fluffybird/image/ui2.jpg"

# ✅ Path asset นก
BIRD_ASSET_PATH = "C:/Users/Cee/Documents/maya/2025/scripts/Fluffybird/ASSET/thedog.ma"

def get_maya_main_window():
    main_window_ptr = Fbui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)

def import_bird_asset():
    if not os.path.exists(BIRD_ASSET_PATH):
        cmds.warning(f"Bird asset file not found: {BIRD_ASSET_PATH}")
        return None

    before = set(cmds.ls(assemblies=True))
    cmds.file(BIRD_ASSET_PATH, i=True, type="mayaAscii", ignoreVersion=True, ra=True,
              mergeNamespacesOnClash=False, namespace="birdAsset")
    after = set(cmds.ls(assemblies=True))

    new_objects = list(after - before)
    if not new_objects:
        cmds.warning("No new object imported from bird asset.")
        return None

    bird_obj = new_objects[0]
    if cmds.objExists("bird"):
        cmds.delete("bird")
    cmds.rename(bird_obj, "bird")
    return "bird"

class FluffyBirdGameUI(QtWidgets.QDialog):
    def __init__(self):
        super(FluffyBirdGameUI, self).__init__(parent=get_maya_main_window())
        self.setWindowTitle("Fluffy Bird")
        self.setFixedSize(300, 330)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.setStyleSheet(
            '''
                }
                QDialog {
                    background-color: white;
                    color: black;
                    font-family: Arial;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: white;
                    color: black;
                    font-family: Arial;
                    border: 3px solid #aaa;
                    padding: 5px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: black;
                    color: white;
                }
                QLabel {
                    color: #333;
                }
        '''
        )

        self.bird = None
        self.pipes = []
        self.gravity = -0.3
        self.jump_force = 0.8
        self.vertical_speed = 0
        self.timer = QtCore.QTimer()
        self.pipe_timer = 0
        self.is_game_running = False
        self.score = 0

        self.create_ui()
        self.create_connections()

    def create_ui(self):
        self.start_btn = QtWidgets.QPushButton("Start Game")
        self.jump_btn = QtWidgets.QPushButton("Jump")
        self.jump_btn.setEnabled(False)
        self.quit_btn = QtWidgets.QPushButton("Quit Game")  # ✅ ปุ่มใหม่

        self.status_label = QtWidgets.QLabel("Press Start to begin")
        self.score_label = QtWidgets.QLabel("Score: 0")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.jump_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.score_label)

        # ✅ QLabel สำหรับแสดงภาพ UI
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.image_label)

        layout.addStretch()
        layout.addWidget(self.quit_btn)

        # ✅ เริ่มต้นด้วยภาพ ui1
        self.update_image(IMAGE_PATH_PLAYING)

    def update_image(self, image_path):
        if os.path.exists(image_path):
            pixmap = QtGui.QPixmap(image_path)
            pixmap = pixmap.scaled(300, 1000, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            print(f"⚠️ Image not found: {image_path}")

    def create_connections(self):
        self.start_btn.clicked.connect(self.start_game)
        self.jump_btn.clicked.connect(self.jump)
        self.quit_btn.clicked.connect(self.quit_game)
        self.timer.timeout.connect(self.update_game)

    def start_game(self):
        self.reset_scene()
        self.vertical_speed = 0
        self.score = 0
        self.pipe_timer = 0
        self.is_game_running = True
        self.score_label.setText("Score: 0")
        self.status_label.setText("Game Running...")
        self.jump_btn.setEnabled(True)

        cmds.lookThru('front')
        cmds.viewFit(all=True)

        front_camera = cmds.modelEditor(cmds.playblast(activeEditor=True), q=True, camera=True)
        cam_pos = cmds.getAttr(f"{front_camera}.translate")[0]
        cmds.setAttr(f"{front_camera}.translate", cam_pos[0], cam_pos[1] + 7.5, cam_pos[2])

        self.bird = import_bird_asset()
        if not self.bird:
            self.status_label.setText("❌ Failed to load bird asset")
            self.is_game_running = False
            return

        cmds.move(0, 5, 0, self.bird)
        self.timer.start(50)

        # ✅ เปลี่ยนเป็นภาพ UI ขณะเล่น
        self.update_image(IMAGE_PATH_PLAYING)

    def quit_game(self):
        """ปิดเกมและล้างทุกอย่างออกจาก scene"""
        # หยุด timer ก่อน
        self.timer.stop()
        self.is_game_running = False

        # ลบ bird และ pipe ทั้งหมดออกจาก Maya scene
        if cmds.objExists("bird"):
            cmds.delete("bird")

        for pipe_pair in self.pipes:
            for pipe in pipe_pair:
                if cmds.objExists(pipe):
                    cmds.delete(pipe)
        self.pipes = []

        # ปิด UI ตัวนี้
        self.close()

    def jump(self):
        if self.is_game_running:
            self.vertical_speed = self.jump_force

    def update_game(self):
        if not self.is_game_running:
            return

        self.vertical_speed += self.gravity
        pos = cmds.xform(self.bird, q=True, translation=True)
        new_y = pos[1] + self.vertical_speed
        cmds.move(pos[0], new_y, pos[2], self.bird)

        if new_y <= 0 or new_y >= 15:
            self.game_over()
            return

        for pipe_pair in self.pipes:
            for pipe in pipe_pair:
                cmds.move(-0.5, 0, 0, pipe, relative=True)

        for pipe_pair in self.pipes[:]:
            x = cmds.xform(pipe_pair[0], q=True, translation=True)[0]
            if x < -10:
                for pipe in pipe_pair:
                    cmds.delete(pipe)
                self.pipes.remove(pipe_pair)
                self.score += 1
                self.score_label.setText(f"Score: {self.score}")

        self.pipe_timer += 1
        if self.pipe_timer >= 20:
            self.pipe_timer = 0
            self.spawn_pipe()

        bird_pos = cmds.xform(self.bird, q=True, translation=True)
        for pipe_pair in self.pipes:
            for pipe in pipe_pair:
                pipe_pos = cmds.xform(pipe, q=True, translation=True)
                pipe_scale = cmds.getAttr(f"{pipe}.scale")[0]
                pipe_height = pipe_scale[1]
                pipe_width = pipe_scale[0]

                if (abs(pipe_pos[0] - bird_pos[0]) < (pipe_width / 2 + 0.5) and
                    abs(pipe_pos[1] - bird_pos[1]) < (pipe_height / 2 + 0.5)):
                    self.game_over()
                    return

    def spawn_pipe(self):
        gap = 4.0
        center = random.uniform(5, 10)

        top_height = 15 - (center + gap / 2)
        bottom_height = center - gap / 2

        top = cmds.polyCube(name="pipe_top", height=top_height, width=2, depth=2)[0]
        cmds.move(10, 15 - top_height / 2, 0, top)

        bottom = cmds.polyCube(name="pipe_bottom", height=bottom_height, width=2, depth=2)[0]
        cmds.move(10, bottom_height / 2, 0, bottom)

        self.pipes.append((top, bottom))

    def game_over(self):
        self.timer.stop()
        self.is_game_running = False
        self.status_label.setText("💀 Game Over!")
        self.jump_btn.setEnabled(False)

        # ✅ เปลี่ยนเป็นภาพ UI Game Over
        self.update_image(IMAGE_PATH_GAMEOVER)

    def reset_scene(self):
        if cmds.objExists("bird"):
            cmds.delete("bird")
        for pipe_pair in self.pipes:
            for pipe in pipe_pair:
                if cmds.objExists(pipe):
                    cmds.delete(pipe)
        self.pipes = []

def show_fluffy_bird_game():
    global fluffy_window

    try:
        fluffy_window.close()
        fluffy_window.deleteLater()
    except:
        pass

    fluffy_window = FluffyBirdGameUI()
    fluffy_window.show()


# ✅ เรียกแสดงเกม
show_fluffy_bird_game()
