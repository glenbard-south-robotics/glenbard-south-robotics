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


class DriveEncoderOdometry(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-1, 5, 1], y_range=[-1, 4, 1],
            x_length=8, y_length=6,
            axis_config={"include_tip": True},
        )
        labels = axes.get_axis_labels(MathTex("x"), MathTex("y"))
        self.play(Create(axes), Write(labels))

        pose = np.array([0.0, 0.0, 0.0])   # x, y, theta

        steps = [
            (80, 120),
            (100, 100),
            (120, 60),
            (100, 100),
            (150, 490)
        ]
        TICKS_PER_MM = 8.0
        W_MM         = 300.0

        robot_dot = Dot(axes.c2p(pose[0], pose[1]), color=YELLOW, radius=0.08)
        heading   = Arrow(
            axes.c2p(pose[0], pose[1]),
            axes.c2p(pose[0] + 0.4 * np.cos(pose[2]),
                     pose[1] + 0.4 * np.sin(pose[2])),
            buff=0, color=YELLOW, stroke_width=3,
        )
        self.play(Create(robot_dot), Create(heading))

        trace = VMobject(color=BLUE, stroke_width=2)
        trace.set_points_as_corners([axes.c2p(pose[0], pose[1])] * 2)
        self.add(trace)

        for dL, dR in steps:
            dL_mm = dL / TICKS_PER_MM / 100
            dR_mm = dR / TICKS_PER_MM / 100
            W     = W_MM / TICKS_PER_MM / 100

            ds     = (dL_mm + dR_mm) / 2
            dtheta = (dR_mm - dL_mm) / W
            mid    = pose[2] + dtheta / 2

            new_pose = pose.copy()
            new_pose[0] += ds * np.cos(mid)
            new_pose[1] += ds * np.sin(mid)
            new_pose[2] += dtheta

            arc_label = MathTex(
                rf"\Delta s={ds*100:.1f}\;\Delta\theta={np.degrees(dtheta):.1f}°"
            ).to_corner(UL, buff=0.4).scale(0.6)

            new_dot     = axes.c2p(new_pose[0], new_pose[1])
            new_heading = Arrow(
                new_dot,
                axes.c2p(new_pose[0] + 0.4 * np.cos(new_pose[2]),
                         new_pose[1] + 0.4 * np.sin(new_pose[2])),
                buff=0, color=YELLOW, stroke_width=3,
            )
            trace.add_points_as_corners([new_dot])

            self.play(
                robot_dot.animate.move_to(new_dot),
                Transform(heading, new_heading),
                Write(arc_label),
                run_time=0.8,
            )
            self.play(FadeOut(arc_label), run_time=0.3)
            pose = new_pose

        self.wait(2)

class DeadWheelConfig(Scene):
    def construct(self):
        chassis = Rectangle(width=2.8, height=3.2, color=GRAY,
                            fill_color=DARK_GRAY, fill_opacity=0.4)
        self.play(Create(chassis))

        wL = Rectangle(width=0.25, height=0.7, color=GREEN,
                       fill_color=GREEN, fill_opacity=0.9).move_to(LEFT * 1.4)
        wR = Rectangle(width=0.25, height=0.7, color=GREEN,
                       fill_color=GREEN, fill_opacity=0.9).move_to(RIGHT * 1.4)

        wS = Rectangle(width=0.7, height=0.25, color=RED,
                       fill_color=RED, fill_opacity=0.9).move_to(UP * 0.8)
        self.play(Create(wL), Create(wR), Create(wS))

        lL = MathTex(r"\Delta L", color=GREEN).next_to(wL, LEFT, buff=0.15).scale(0.7)
        lR = MathTex(r"\Delta R", color=GREEN).next_to(wR, RIGHT, buff=0.15).scale(0.7)
        lS = MathTex(r"\Delta S", color=RED).next_to(wS, UP, buff=0.15).scale(0.7)
        self.play(Write(lL), Write(lR), Write(lS))

        b_line = DoubleArrow(LEFT * 1.4 + DOWN * 1.2,
                             RIGHT * 1.4 + DOWN * 1.2,
                             buff=0, color=YELLOW, stroke_width=2)
        b_label = MathTex("2b", color=YELLOW).next_to(b_line, DOWN, buff=0.2).scale(0.65)

        rs_line = DoubleArrow(ORIGIN + DOWN * 0.05,
                              UP * 0.8 + DOWN * 0.05,
                              buff=0, color=BLUE, stroke_width=2)
        rs_label = MathTex("r_S", color=BLUE).next_to(rs_line, RIGHT, buff=0.1).scale(0.65)

        centre_dot = Dot(ORIGIN, color=WHITE, radius=0.06)
        centre_label = MathTex(r"\text{CoR}").next_to(centre_dot, RIGHT, buff=0.1).scale(0.6)

        self.play(Create(b_line), Write(b_label),
                  Create(rs_line), Write(rs_label),
                  Create(centre_dot), Write(centre_label))

        formula = MathTex(
            r"\Delta\theta = \frac{\Delta R - \Delta L}{2b}"
        ).to_corner(UL, buff=0.4).scale(0.75)
        self.play(Write(formula))
        self.wait(2)


class PinpointMount(Scene):
    def construct(self):
        chassis = Rectangle(width=3.5, height=3.5, color=GRAY,
                            fill_color=DARK_GRAY, fill_opacity=0.35)
        self.play(Create(chassis))

        pcb = Rectangle(width=0.8, height=0.5, color=TEAL,
                        fill_color=TEAL, fill_opacity=0.7).move_to(RIGHT * 0.9 + UP * 0.6)
        pcb_label = Tex("Pinpoint", font_size=20, color=TEAL).next_to(pcb, UP, buff=0.08)
        self.play(Create(pcb), Write(pcb_label))

        podY = Rectangle(width=0.25, height=0.55, color=GREEN,
                         fill_color=GREEN, fill_opacity=0.8).move_to(LEFT * 1.5 + UP * 0.6)
        podX = Rectangle(width=0.55, height=0.25, color=RED,
                         fill_color=RED, fill_opacity=0.8).move_to(RIGHT * 0.9 + DOWN * 1.4)

        podY_label = MathTex(r"\parallel", color=GREEN).next_to(podY, LEFT, buff=0.1).scale(0.8)
        podX_label = MathTex(r"\perp",    color=RED  ).next_to(podX, DOWN, buff=0.1).scale(0.8)
        self.play(Create(podY), Create(podX), Write(podY_label), Write(podX_label))

        xOff = DoubleArrow(ORIGIN, RIGHT * 0.9, buff=0, color=RED, stroke_width=1)
        xOff_label = MathTex(r"x_\text{off}", color=RED).next_to(xOff, DOWN, buff=0.08).scale(0.65)
        yOff = DoubleArrow(ORIGIN, UP * 0.6, buff=0, color=GREEN, stroke_width=1)
        yOff_label = MathTex(r"y_\text{off}", color=GREEN).next_to(yOff, LEFT, buff=0.08).scale(0.65)

        self.play(Create(xOff), Write(xOff_label), Create(yOff), Write(yOff_label))
        self.wait(2)
