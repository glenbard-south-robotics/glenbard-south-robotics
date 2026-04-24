import math
from manim import *  # pyright: ignore[reportWildcardImportFromLibrary]

class VectorErrorFunction(Scene):
    def construct(self):
        arm_radius = 2
        vec_a_angle = PI / 2   # desired: straight up
        vec_b_angle = PI / 4   # current: 45 degrees

        vec_a = Vector(
            (math.sin(vec_a_angle) * arm_radius,
             math.cos(vec_a_angle) * arm_radius),
            color=GREEN
        )
        vec_b = Vector(
            (math.sin(vec_b_angle) * arm_radius,
             math.cos(vec_b_angle) * arm_radius),
            color=RED
        )
        self.play(Create(vec_a), Create(vec_b))

        label_a = MathTex("P_D").next_to(vec_a.get_end(), RIGHT, buff=0.2)
        label_b = MathTex("P_t").next_to(vec_b.get_end(), UP, buff=0.2)
        self.play(Write(label_a), Write(label_b))

        error_vec = Arrow(vec_b.get_end(), vec_a.get_end(), buff=0, color=YELLOW)
        self.play(Create(error_vec))

        error = vec_a.get_end() - vec_b.get_end()
        error_text = MathTex(
            rf"e(t) = P_D - P_t = \begin{{pmatrix}} {error[0]:.2f} \\ {error[1]:.2f} \end{{pmatrix}}"
        ).to_corner(UL, buff=0.5)
        self.play(Write(error_text))

        arc = Arc(
            start_angle=PI / 2 - vec_b_angle,
            angle=vec_b_angle - vec_a_angle,
            radius=0.7,
            color=BLUE
        )
        arc_label = MathTex(r"\Delta \theta").move_to(
            arc.point_from_proportion(0.5) + RIGHT * 0.5
        )
        self.play(Create(arc), Write(arc_label))
        self.wait(2)

class PControllerComparison(Scene):
    def construct(self):
        axes_left = Axes(
            x_range=[0, 6, 1],
            y_range=[-0.1, 1.8, 0.2],
            x_length=5,
            y_length=3,
            axis_config={"include_tip": True},
        ).to_edge(LEFT, buff=0.8)

        axes_right = axes_left.copy().to_edge(RIGHT, buff=0.8)

        title_left = MathTex(r"\text{First-Order System}").scale(0.6).next_to(axes_left, UP)
        title_right = MathTex(r"\text{Second-Order System}").scale(0.6).next_to(axes_right, UP)

        self.play(Create(axes_left), Create(axes_right))
        self.play(Write(title_left), Write(title_right))

        setpoint_left = axes_left.plot(lambda _: 1.0, color=WHITE, stroke_width=1)
        setpoint_right = axes_right.plot(lambda _: 1.0, color=WHITE, stroke_width=1)

        self.play(Create(setpoint_left), Create(setpoint_right))

        def simulate_first_order(kp, dt=0.01, T=6.0):
            x, t = 0.0, 0.0
            xs, ts = [x], [t]
            while t < T:
                u = kp * (1.0 - x)
                x += dt * (u - 0.5 * x)
                t += dt
                xs.append(x); ts.append(t)
            return ts, xs

        def simulate_second_order(kp, dt=0.01, T=6.0):
            x, v, t = 0.0, 0.0, 0.0
            xs, ts = [x], [t]
            while t < T:
                u = kp * (1.0 - x)
                v += dt * (u - 0.8 * v)  # damping term
                x += dt * v
                t += dt
                xs.append(x); ts.append(t)
            return ts, xs

        configs = [
            (0.5, BLUE),
            (2.0, GREEN),
            (6.0, YELLOW),
            (12.0, RED),
        ]

        for kp, color in configs:
            ts1, xs1 = simulate_first_order(kp)
            ts2, xs2 = simulate_second_order(kp)

            curve1 = axes_left.plot_line_graph(
                ts1, xs1,
                add_vertex_dots=False,
                line_color=color,
                stroke_width=2.5,
            )

            curve2 = axes_right.plot_line_graph(
                ts2, xs2,
                add_vertex_dots=False,
                line_color=color,
                stroke_width=2.5,
            )

            self.play(
                Create(curve1),
                Create(curve2),
                run_time=1.2
            )

        note_left = MathTex(
            r"\text{No overshoot, exponential approach}"
        ).scale(0.5).next_to(axes_left, DOWN)

        note_right = MathTex(
            r"\text{Overshoot \& oscillation appear}"
        ).scale(0.5).next_to(axes_right, DOWN)

        self.play(Write(note_left), Write(note_right))
        self.wait(2)

class IntegralWindup(Scene):
    """
    Shows how the integral eliminates steady-state error but winds up without clamping.
    """
    def construct(self):
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[-0.2, 2.0, 0.2],
            x_length=10,
            y_length=5,
            axis_config={"include_tip": True},
        )
        labels = axes.get_axis_labels(MathTex("t"), MathTex("x(t)"))
        setpoint = axes.plot(lambda _: 1.0, color=WHITE, stroke_width=1)
        self.play(Create(axes), Write(labels), Create(setpoint))

        def simulate(ki, clamp=False, dt=0.02, T=10.0):
            x, integral = 0.0, 0.0
            disturbance  = 0.3
            xs, ts       = [x], [0.0]
            t            = 0.0
            while t < T:
                e        = 1.0 - x
                integral += e * dt
                if clamp:
                    integral = max(-2.0, min(2.0, integral))
                u  = 0.5 * e + ki * integral - disturbance
                x += dt * (u - 0.4 * x)
                t += dt
                xs.append(x); ts.append(t)
            return ts, xs

        configs = [
            (0.0, False, BLUE,   r"K_I=0\;\text{(P only, steady-state-error)}"),
            (0.3, False, GREEN,  r"K_I=0.3\;\text{(eliminates offset)}"),
            (0.3, True,  YELLOW, r"K_I=0.3\;\text{(clamped)}"),
            (1.5, False, RED,    r"K_I=1.5\;\text{(windup)}"),
        ]

        legend = VGroup()
        for ki, clamp, color, tex in configs:
            ts, xs = simulate(ki, clamp)
            curve = axes.plot_line_graph(
                x_values=ts, y_values=xs,
                add_vertex_dots=False, line_color=color, stroke_width=2.5,
            )
            item = VGroup(
                Line(LEFT * 0.3, RIGHT * 0.3, color=color, stroke_width=2.5),
                MathTex(tex, color=color).scale(0.52),
            ).arrange(RIGHT, buff=0.15)
            legend.add(item)
            self.play(Create(curve), run_time=1.2)

        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UR, buff=0.4)
        self.play(FadeIn(legend))
        self.wait(2)


class DerivativeEffect(Scene):
    """
    Shows how increasing K_D damps overshoot, then overdamps the response.
    """
    def construct(self):
        axes = Axes(
            x_range=[0, 8, 1],
            y_range=[-0.2, 1.8, 0.2],
            x_length=10,
            y_length=5,
            axis_config={"include_tip": True},
        )
        labels = axes.get_axis_labels(MathTex("t"), MathTex("x(t)"))
        setpoint = axes.plot(lambda _: 1.0, color=WHITE, stroke_width=1)
        self.play(Create(axes), Write(labels), Create(setpoint))

        def simulate(kp, kd, dt=0.01, T=8.0):
            x, v   = 0.0, 0.0
            prev_e = 1.0
            xs, ts = [x], [0.0]
            t      = 0.0
            while t < T:
                e      = 1.0 - x
                de_dt  = (e - prev_e) / dt
                u      = kp * e + kd * de_dt
                a      = u - 0.3 * v
                v     += dt * a
                x     += dt * v
                prev_e = e
                t     += dt
                xs.append(x); ts.append(t)
            return ts, xs

        configs = [
            (5.0, 0.0, BLUE,   r"K_D=0\;\text{(overshoot)}"),
            (5.0, 0.5, GREEN,  r"K_D=0.5"),
            (5.0, 2.0, YELLOW, r"K_D=2.0\;\text{(well damped)}"),
            (5.0, 8.0, RED,    r"K_D=8.0\;\text{(overdamped)}"),
        ]

        legend = VGroup()
        for kp, kd, color, tex in configs:
            ts, xs = simulate(kp, kd)
            curve = axes.plot_line_graph(
                x_values=ts, y_values=xs,
                add_vertex_dots=False, line_color=color, stroke_width=2.5,
            )
            item = VGroup(
                Line(LEFT * 0.3, RIGHT * 0.3, color=color, stroke_width=2.5),
                MathTex(tex, color=color).scale(0.55),
            ).arrange(RIGHT, buff=0.15)
            legend.add(item)
            self.play(Create(curve), run_time=1.0)

        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UR, buff=0.4)
        self.play(FadeIn(legend))
        self.wait(2)

class FullPIDComparison(Scene):
    """
    Compares P, PD, PI, and full PID on a second-order plant with a load disturbance.
    """
    def construct(self):
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[-0.1, 1.6, 0.2],
            x_length=10,
            y_length=5,
            axis_config={"include_tip": True},
        )
        labels = axes.get_axis_labels(MathTex("t\\ (\\text{s})"), MathTex("x(t)"))
        setpoint = axes.plot(lambda _: 1.0, color=WHITE, stroke_width=1)
        self.play(Create(axes), Write(labels), Create(setpoint))

        def simulate(kp, ki, kd, dt=0.01, T=10.0):
            x, v       = 0.0, 0.0
            integral   = 0.0
            prev_e     = 1.0
            disturbance = 0.25
            xs, ts     = [x], [0.0]
            t          = 0.0
            while t < T:
                e         = 1.0 - x
                integral  = max(-1.0, min(1.0, integral + e * dt))
                de_dt     = (e - prev_e) / dt
                u         = kp * e + ki * integral + kd * de_dt - disturbance
                a         = u - 0.4 * v
                v        += dt * a
                x        += dt * v
                prev_e    = e
                t        += dt
                xs.append(x); ts.append(t)
            return ts, xs

        configs = [
            (3.0, 0.0, 0.0, BLUE,   r"\text{P only (steady-state-error)}"),
            (3.0, 0.0, 1.2, GREEN,  r"\text{PD (damped, steady-state-error persists)}"),
            (3.0, 0.8, 0.0, YELLOW, r"\text{PI (no steady-state-error, overshoot)}"),
            (3.0, 0.8, 1.2, RED,    r"\text{PID (full)}"),
        ]

        legend = VGroup()
        for kp, ki, kd, color, tex in configs:
            ts, xs = simulate(kp, ki, kd)
            curve = axes.plot_line_graph(
                x_values=ts, y_values=xs,
                add_vertex_dots=False, line_color=color, stroke_width=2.5,
            )
            item = VGroup(
                Line(LEFT * 0.3, RIGHT * 0.3, color=color, stroke_width=2.5),
                MathTex(tex, color=color).scale(0.58),
            ).arrange(RIGHT, buff=0.15)
            legend.add(item)
            self.play(Create(curve), run_time=1.2)

        legend.arrange(DOWN, aligned_edge=RIGHT, buff=0.25).to_corner(UR, buff=0.2)
        self.play(FadeIn(legend))
        self.wait(2)
