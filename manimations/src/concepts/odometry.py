from manim import *  # pyright: ignore[reportWildcardImportFromLibrary]
import numpy as np

class PoseVector(Scene):
    """
    Draws a top-down field view and animates the robot's pose (x, y, theta)
    updating as it follows a curved path.
    """
    def construct(self):
        field = Square(side_length=6, color=GRAY, fill_opacity=0.08)
        x_axis = Arrow(LEFT * 3.2, RIGHT * 3.2, buff=0, color=WHITE, stroke_width=1.5)
        y_axis = Arrow(DOWN * 3.2, UP * 3.2, buff=0, color=WHITE, stroke_width=1.5)
        x_label = MathTex("x").next_to(x_axis.get_end(), RIGHT, buff=0.1).scale(0.7)
        y_label = MathTex("y").next_to(y_axis.get_end(), UP,    buff=0.1).scale(0.7)
        self.play(Create(field), Create(x_axis), Create(y_axis),
                  Write(x_label), Write(y_label))

        robot = Arrow((np.cos(0) * 2 - 2, np.sin(0) * 2 - 2, 0), (np.cos(0) * 2 - 2, np.sin(0) * 2 - 2, 0) + UP * 0.5, buff=0, color=YELLOW, stroke_width=4)
        robot_dot = Dot((np.cos(0) * 2 - 2, np.sin(0) * 2 - 2, 0), color=YELLOW, radius=0.08)
        self.play(Create(robot), Create(robot_dot))

        path_points = []
        for t in np.linspace(0, PI / 2, 40):
            path_points.append(np.array([np.cos(t) * 2 - 2, np.sin(t) * 2 - 2, 0]))

        path_mob = VMobject(color=BLUE, stroke_width=1.5, stroke_opacity=0.5)
        path_mob.set_points_smoothly(path_points)
        self.play(Create(path_mob), run_time=0.5)

        pose_label = always_redraw(lambda: MathTex(
            rf"\mathbf{{q}} = ({robot.get_start()[0]:.2f},\ "
            rf"{robot.get_start()[1]:.2f},\ \theta)"
        ).to_corner(UL, buff=0.4).scale(0.65))
        self.add(pose_label)

        for i in range(1, len(path_points)):
            prev = path_points[i - 1]
            curr = path_points[i]
            d    = curr - prev
            angle = np.arctan2(d[1], d[0])
            tip   = curr + np.array([np.cos(angle), np.sin(angle), 0]) * 0.5
            # new_arrow = Arrow(curr, tip, buff=0, color=YELLOW, stroke_width=4)
            self.play(
                robot.animate.put_start_and_end_on(curr, tip),
                robot_dot.animate.move_to(curr),
                run_time=0.04,
                rate_func=linear,
            )
        self.wait(2)
