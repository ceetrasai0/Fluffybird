try:
	from PySide6 import QtCore, QtGui, QtWidgets
	from shiboken6 import wrapInstance
except:
	from PySide2 import QtCore, QtGui, QtWidgets
	from shiboken2 import wrapInstance
import maya.OpenMayaUI as Fbui
import maya.cmds as cmds
import random

def get_maya_main_window():
    main_window_ptr = Fbui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)

class FlappyBirdGameUI(QtWidgets.QDialog):
    def __init__(self):
        super(FlappyBirdGameUI, self).__init__(parent=get_maya_main_window())
        self.setWindowTitle("Flappy Bird in Maya")
        self.setFixedSize(300, 180)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

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
        self.status_label = QtWidgets.QLabel("Press Start to begin")
        self.score_label = QtWidgets.QLabel("Score: 0")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.jump_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.score_label)

    def create_connections(self):
        self.start_btn.clicked.connect(self.start_game)
        self.jump_btn.clicked.connect(self.jump)
        self.timer.timeout.connect(self.update_game)

    def start_game(self):
        self.reset_scene()
        self.vertical_speed = 0
        self.score = 0
        self.is_game_running = True
        self.score_label.setText("Score: 0")
        self.status_label.setText("Game Running...")
        self.jump_btn.setEnabled(True)

        self.bird = cmds.polySphere(name="bird")[0]
        cmds.move(0, 5, 0, self.bird)

        self.timer.start(50)

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
                pipe_scale = cmds.xform(pipe, q=True, scale=True)
                pipe_height = pipe_scale[1] * 1 
                pipe_width = pipe_scale[0] * 1 

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

    def reset_scene(self):
        if cmds.objExists("bird"):
            cmds.delete("bird")
        for pipe_pair in self.pipes:
            for pipe in pipe_pair:
                if cmds.objExists(pipe):
                    cmds.delete(pipe)
        self.pipes = []

def show_flappy_bird_game():
    for widget in QtWidgets.QApplication.allWidgets():
        if isinstance(widget, FlappyBirdGameUI):
            widget.close()
    win = FlappyBirdGameUI()
    win.show()

show_flappy_bird_game()