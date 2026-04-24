---
title: PID Controllers
tags:
  - concepts
---
PID controllers are one of the most widely used feedback control algorithms in engineering. They appear everywhere, in FTC you will use them to smoothly and accurately drive motors to a target position, hold a drivetrain heading, or regulate arm speed.

The name is an acronym of its three terms: **Proportional**, **Integral**, and **Derivative**.

# The Full Equation

>[!note]
> Calculus is not required to understand PID controllers, but a passing knowledge of derivatives and integrals will make this concept click easier.

$$
u(t) = K_Pe(t) + K_I\int^{t}_{0}e(\tau)d\tau + K_D\frac{de(t)}{dt}
$$

Where $u(t)$ is the **control output** — in FTC this is typically a value passed to `motor.setPower()`, clamped to $[−1, 1]$. The signal $e(t)$ is the **error**, a measure of how far the system is from its target. Each gain $K_P$​, $K_I$​, $K_D$​ is a constant that scales its respective term.

## The Error Function $e(t)$

Before a controller can correct a system, it needs to measure how wrong it is. Errors is defined as the difference between the **desired** state and the **current** state:

$$
e(t) = P_D - P_t
$$

$P_D$ is the desired position, and $P_t$ is the current measured position. In a 1-dimensional motor controller, both are measured in tick counts — read from `motor.getCurrentPosition()`.

For example, if the desired position is 1000 ticks, and the current position is 350 ticks:

$$
e(t) = 1000 - 350 = 650 \ ticks
$$

In 2-dimensions — both quantities become vectors, and $e(t)$ points from where the arm *is* to where it *should be*.

<video autoplay muted playsinline controls>  
<source src="/static/videos/concepts/pid/VectorErrorFunction.webm" type="video/webm">  
</video>
In Kotlin, computing the error for a motor is a single line:

```kotlin
val error = targetPosition - motor.currentPosition
```

## The Proportional Term (P)

$$
u_P(t) = K_P \ \cdot \ e(t)
$$

The proportional term produces an output **directly proportional to the current error**. Large error -> large correction. Small error -> small correction. The gain $K_P$ sets the aggressiveness of the response. 

---

**The problem with P alone:**  
Against any constant opposing force — such as gravity on an arm or drivetrain friction — a pure P controller settles at a point where its output balances the disturbance. The system stops moving, but the error is not zero. This is called **steady-state error**.

Increasing $K_P$​ reduces this error by making the controller more aggressive. However, in real systems with inertia (like motors and arms), high $K_P$​ can cause the system to **overshoot the target and oscillate**. This behavior comes from the system’s dynamics, not the P term alone.

Oscillation happens because the system has inertia—it keeps moving after the controller tells it to stop. The controller then overcorrects in the opposite direction, creating a cycle.
<video autoplay muted playsinline controls>  
<source src="/static/videos/concepts/pid/PControllerComparison.webm" type="video/webm">  
</video>

A proportional controller is like a spring: the farther you stretch it, the harder it pulls back—but it doesn’t know anything about momentum.

In Kotlin, the P term maps directly to `setPower`:
```kotlin
val KP = 0.005 // tuned for your specific motor + load 
val error = targetPosition - motor.currentPosition 
val output = (KP * error).coerceIn(-1.0, 1.0) 

motor.power = output
```

> `coerceIn(-1.0, 1.0)` clamps the result to the valid motor power range. Without clamping, the math can produce values that the hardware ignores.

## The Integral Term (I)

>[!info]
> In many FTC applications, a well-tuned PD controller with feedforward is sufficient. The integral term is mainly useful when you must eliminate small steady-state errors under unpredictable loads.

$$
u_I(t) = K_I \cdot \int^{t}_{0}e(\tau)d\tau
$$

The integral term **accumulates error over time**. If the system sits with a small persistent offset — exactly the weakness of the P term — the integral keeps growing, continuously pushing the output until the error is eliminated.

**Discretely**, the integral is approximated as a running sum:

$$
I_k = I_{k - 1} + e_k \cdot \Delta t
$$  
where $\Delta$ is the time elapsed since the last loop, obtainable from `ElapsedTime`.

**The problem with I:** Too much integral gain causes **windup** — the accumulator grows very large during a long approach, then massively overshoots when the target is reached. The standard fix is to **clamp** the integrator: stop accumulating once the integral term alone would saturate the output.

<video autoplay muted playsinline controls>  
<source src="/static/videos/concepts/pid/IntegralWindup.webm" type="video/webm">  
</video>

In Kotlin, the integral is a running sum maintained between loop iterations:

```kotlin
val KP = 0.005 
val KI = 0.0001 
val INTEGRAL_MAX = 0.4 // anti-windup max 
var integralSum = 0.0 

var lastTime = System.nanoTime() 

// --- inside a loop --- 
val now = System.nanoTime() 
val dt = (now - lastTime) / 1_000_000_000.0 // convert ns -> seconds 
lastTime = now

val error = targetPosition - motor.currentPosition 
integralSum = (integralSum + error * dt).coerceIn(-INTEGRAL_MAX, INTEGRAL_MAX)

val output = (KP * error + KI * integralSum).coerceIn(-1.0, 1.0)
motor.power = output
```

## The Derivative Term (D)

$$
u_D(t) = K_D \cdot \frac{de(t)}{dt}
$$

The derivative term reacts to the **rate of change of error**. If the error is shrinking rapidly — the system is already moving toward the target — the derivative applies a braking force to prevent overshoot. If the error is suddenly growing fast, it responds immediately before the slower P and I terms have time to build up. 

**Discretely**, the derivative is approximated as a finite difference:

$$
\frac{de}{dt} \approx \frac{e_k - e_{k - 1}}{\Delta t}
$$

**The problem with D:** Derivative control amplifies noise. A jittery encoder makes $\frac{de}{dt}$​ jump wildly, producing erratic spikes. The standard remedy is to differentiate the **measured position** directly (not the error) and apply a **low-pass filter** to smooth the result.

<video autoplay muted playsinline controls>  
<source src="/static/videos/concepts/pid/DerivativeEffect.webm" type="video/webm">  
</video>

In Kotlin, the derivative is the difference between consecutive errors divided by elapsed time:

```kotlin
val KP = 0.005 
val KD = 0.0003 

var lastError = 0 
var lastTime = System.nanoTime() 

// --- inside a loop ---
val now = System.nanoTime()
val dt = (now - lastTime) / 1_000_000_000.0 // ns -> s
lastTime = now 

val error = targetPosition - motor.currentPosition 
val dedt = if (dt > 0) (error - lastError) / dt else 0.0 
lastError = error 

val output = (KP * error + KD * dedt).coerceIn(-1.0, 1.0) 
motor.power = output
```


Combining all three terms gives the complete controller:

$$
 u(t) = \underbrace{K_P e(t)}_{\text{present}} +\; \underbrace{K_I \int_0^t e(\tau)\, d\tau}_{\text{past}} +\; \underbrace{K_D \frac{de(t)}{dt}}_{\text{future}}
$$

Each term addresses a different part of time — P reacts now, I corrects the history of error. 

> [!important]  
> P is position (how far you are)  
> D is velocity (how fast you're moving)

<video autoplay muted playsinline controls>  
<source src="/static/videos/concepts/pid/FullPIDComparison.webm" type="video/webm">  
</video>

A complete, reusable PID class in Kotlin for FTC:

```kotlin
import com.qualcomm.robotcore.util.ElapsedTime

/**
 * A simple PID controller suitable for FTC motor position control.
 *
 * Usage:
 *   val pid = PIDController(kP = 0.005, kI = 0.0001, kD = 0.0003)
 *   // inside your loop:
 *   motor.power = pid.calculate(target = 1000, measured = motor.currentPosition)
 */
class PIDController(
    val kP: Double,
    val kI: Double,
    val kD: Double,
    val integralMax: Double = 0.4,   // anti-windup magnitude
    val outputMax:   Double = 1.0,   // max motor power
) {
    private var integralSum = 0.0
    private var lastError   = 0.0
    private val timer       = ElapsedTime()

    fun calculate(target: Int, measured: Int): Double {
        val dt    = timer.seconds().also { timer.reset() }
        val error = (target - measured).toDouble()

        integralSum = (integralSum + error * dt).coerceIn(-integralMax, integralMax)
        
        val velocity = (measured - lastMeasured) / dt  
        val derivative = -velocity  
        lastMeasured = measured

        val output = kP * error + kI * integralSum + kD * derivative
        return output.coerceIn(-outputMax, outputMax)
    }

    /** Call when re-enabling or changing targets to avoid a derivative spike. */
    fun reset() {
        integralSum = 0.0
        lastError   = 0.0
        timer.reset()
    }
}
```

And a minimal `LinearOpMode` showing it in action:

```kotlin
import com.qualcomm.robotcore.eventloop.opmode.LinearOpMode
import com.qualcomm.robotcore.eventloop.opmode.TeleOp
import com.qualcomm.robotcore.hardware.DcMotor
import com.qualcomm.robotcore.hardware.DcMotorSimple

@TeleOp(name = "PID Demo")
class PIDDemoOpMode : LinearOpMode() {

    override fun runOpMode() {
        val motor = hardwareMap.get(DcMotor::class.java, "arm_motor")
        motor.direction = DcMotorSimple.Direction.FORWARD
        motor.mode      = DcMotor.RunMode.STOP_AND_RESET_ENCODER
        motor.mode      = DcMotor.RunMode.RUN_WITHOUT_ENCODER

        val pid          = PIDController(kP = 0.005, kI = 0.0001, kD = 0.0003)
        val targetTicks  = 1000     // desired encoder position

        waitForStart()

        while (opModeIsActive()) {
            val power = pid.calculate(
                target   = targetTicks,
                measured = motor.currentPosition
            )
            motor.power = power

            telemetry.addData("Target",   targetTicks)
            telemetry.addData("Position", motor.currentPosition)
            telemetry.addData("Error",    targetTicks - motor.currentPosition)
            telemetry.addData("Power",    "%.3f".format(power))
            telemetry.update()
        }

        motor.power = 0.0
    }
}
```

# Feedforward

In many FTC systems (arms, elevators), the controller constantly fights predictable forces like gravity. Without feedforward, the PID controller must constantly generate error just to hold position.

Instead of relying on the integral term to “figure it out,” you can add a **feedforward term**:

$$
u(t) = PID  + k_F
$$

```kotlin
val kF = 0.2 // constant to hold arm against gravity  
motor.power = pidOutput + kF
```

Or increase the $k_F$ depending on the angle of the arm:

```kotlin
val kG = 0.2
val kF = cos(angle) * kG
```

# Tuning

>The gains $K_P$, $K_I$, and $K_D$ depend on your units (ticks, seconds, motor power), so they must be tuned for your specific system.

A practical starting procedure for tuning in FTC:

1. Set $K_I=K_D=0$. Raise $K_P$​ until the motor reaches the target quickly, accepting some overshoot.
2. Raise $K_D$​ to damp the overshoot without slowing the initial response excessively.
3. If steady-state error remains under load, introduce a small $K_I$​ and watch carefully for windup.