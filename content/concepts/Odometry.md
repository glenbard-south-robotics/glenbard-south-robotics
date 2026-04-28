---
title: Odometry
tags:
  - concepts
---
Odometry is the process of estimating a robot's **pose** — its position and orientation in space by integrating sensor readings over time. Rather than relying on where you _told_ the robot to go, odometry tracks where it _actually went_. This distinction matters enormously in FTC: wheels slip, tiles compresses unevenly, and motors don't respond identically. Without odometry, positional error accumulates. With it, you can feed corrective signals back into a PID controller and close the loop.

---

# The Pose Vector **q**

In the playing field, the pose vector is described with four numbers:

$$
\mathbf{q} = \left(\begin{array}{c} x \\ y \\ z \\ \theta \end{array}\right) \in \mathbb{R}^4
$$

| Component | Meaning                                                                | Unit              |
| --------- | ---------------------------------------------------------------------- | ----------------- |
| $x$       | Position along the field's horizontal axis                             | mm                |
| $y$       | Position along the field's vertical axis                               | mm                |
| $z$       | Vertical position for lifts or arms.                                   | mm                |
| $\theta$  | Heading — the angle the robot faces, measured from the positive x-axis | radians / degrees |
For a ground-plane drivetrain $z$ is constant and can be dropped, reducing the pose to $(x, y, \theta) \in \mathbb{R}^3$. Once a lift or arm enters the picture, tracking $z$ separately lets you compose the full four-dimensional pose for path-planning purposes.

## The Pose Update Rule

At each control loop iteration, the estimated pose is updated by integrating the incremental displacement $\Delta\mathbf{q}$:

$$
\mathbf{q}_{k + 1} = \mathbf{q}_k + \Delta\mathbf{q}_k 
$$

where $\Delta\mathbf{q}_k$​ is computed differently depending on the odometry hardware in use. The remainder of this page covers three approaches in order of increasing accuracy and complexity.

<video autoplay muted playsinline controls>  
<source src="/static/concepts/odometry/PoseVector.webm" type="video/webm">  
</video>

# Methods

## Drive Encoders

![[UltraplanetaryMotorREV.png]]

The simplest odometry approach uses the encoders that are already built into your drive motors. Every REV motor with an encoder reports a tick count; the change in ticks between loop iterations tells you how far each wheel turned.

### How It Works

For a differential (tank) drivetrain, label the left and right encoder displacements (in ticks) over one loop as $\Delta L$ and $\Delta R$. Converting ticks to distance:

$$
d = \frac{\Delta ticks \times 2\pi r}{N}
$$

where $r$ is the wheel radius and $N$ is the encoder resolution (ticks per revolution). The incremental linear displacement and heading change are then:

$$
\Delta s = \frac{\Delta L + \Delta R}{2}, \qquad \Delta \theta = \frac{\Delta R - \Delta L}{W}
$$
​
where $W$ is the track width (distance between the two drive wheels). Projecting onto the field axes using the *current* heading before the update:

$$
\Delta x = \Delta s \cos\!\left(\theta + \frac{\Delta\theta}{2}\right), \qquad \Delta y = \Delta s \sin\!\left(\theta + \frac{\Delta\theta}{2}\right)
$$

Using $\theta + \frac{\Delta\theta}{2}$ (the heading at the midpoint of the arc) gives the **arc integration** approximation, which is far more accurate than using the heading at either endpoint alone.

### Limitations

Drive encoder odometry degrades whenever the drive wheels **slip** — hard braking, turning sharply on carpet, or pushing against another robot. Since the encoder measures _motor shaft rotation_, not actual wheel-ground contact, any slip goes undetected and accumulates as positional error.

<video autoplay muted playsinline controls>  
<source src="/static/concepts/odometry/DriveEncoderOdometry.webm" type="video/webm">  
</video>

In Kotlin, drive encoder odometry for a differential drivetrain:
```kotlin
import com.qualcomm.robotcore.hardware.DcMotor
import kotlin.math.cos
import kotlin.math.sin

/**
 * Differential-drive odometry using built-in drive motor encoders.
 *
 * @param ticksPerMm    encoder ticks per millimetre of wheel travel
 * @param trackWidthMm  distance between left and right contact patches (mm)
 */
class DriveEncoderOdometry(
    private val ticksPerMm: Double,
    private val trackWidthMm: Double,
) {
    var x:     Double = 0.0   // mm
    var y:     Double = 0.0   // mm
    var theta: Double = 0.0   // radians

    private var lastLeft:  Int = 0
    private var lastRight: Int = 0

    /** Call once after encoders are reset. */
    fun initialize(leftMotor: DcMotor, rightMotor: DcMotor) {
        lastLeft  = leftMotor.currentPosition
        lastRight = rightMotor.currentPosition
    }

    /** Call every loop iteration with current encoder positions. */
    fun update(leftTicks: Int, rightTicks: Int) {
        val dL = (leftTicks  - lastLeft)  / ticksPerMm
        val dR = (rightTicks - lastRight) / ticksPerMm
        lastLeft  = leftTicks
        lastRight = rightTicks

        val ds     = (dL + dR) / 2.0
        val dTheta = (dR - dL) / trackWidthMm
        val mid    = theta + dTheta / 2.0   // arc integration midpoint

        x     += ds * cos(mid)
        y     += ds * sin(mid)
        theta += dTheta
    }
}
```

## Deadwheels

![[GoBuildaDeadwheelsPinpoint.png]]
Dead wheels are unpowered, freely spinning encoder wheels that contact the ground at fixed positions on the robot chassis. Because they carry no drive load they are immune to the wheel slip.
### Three-Wheel Configuration

The standard FTC configuration uses **two parallel wheels** (measuring forward/backward motion) and **one perpendicular wheel** (measuring lateral/strafe motion). Label their displacements over one loop as $\Delta L$, $\Delta R$ (parallel, left and right of center), and $\Delta S$ (lateral):

$$
\Delta \theta = \frac{\Delta R - \Delta L}{2b}
$$


where  $b$ is the half-distance between the two parallel wheels. The forward displacement is the average of the two parallel wheels, corrected for the robot's rotation to remove the arc component:

$$
\Delta_{\parallel} = \frac{\Delta L + \Delta R}{2}, \qquad \Delta_{\perp} = \Delta S - r_S \,\Delta\theta
$$


where $r_S$​ is the signed distance from the robot's center of rotation to the lateral wheel. Projecting onto field coordinates with the arc midpoint heading $\phi = \theta + \frac{\Delta\theta}{2}$​:

$$
\Delta x = \Delta_{\parallel} \cos\phi - \Delta_{\perp} \sin\phi
$$
$$
\Delta y = \Delta_{\parallel} \sin\phi + \Delta_{\perp} \cos\phi
$$

The lateral correction term $r_S\Delta\theta$ is critical — without it, any rotation causes a lateral displacement because the perpendicular wheel is offset from the center.

<video autoplay muted playsinline controls>  
<source src="/static/concepts/odometry/DeadWheelConfig.webm" type="video/webm">  
</video>

In Kotlin, a three-wheel dead-wheel odometer:
```kotlin
import kotlin.math.cos
import kotlin.math.sin

/**
 * Three-wheel dead-wheel odometry.
 *
 * @param ticksPerMm        encoder ticks per mm of wheel arc
 * @param halfTrackMm       half the distance between parallel wheels (b)
 * @param lateralOffsetMm   signed forward distance from CoR to lateral wheel (r_S)
 */
class DeadWheelOdometry(
    private val ticksPerMm: Double,
    private val halfTrackMm: Double,
    private val lateralOffsetMm: Double,
) {
    var x:     Double = 0.0   // mm
    var y:     Double = 0.0   // mm
    var theta: Double = 0.0   // radians

    private var lastLeft:   Int = 0
    private var lastRight:  Int = 0
    private var lastStrafe: Int = 0

    fun initialize(leftTicks: Int, rightTicks: Int, strafeTicks: Int) {
        lastLeft   = leftTicks
        lastRight  = rightTicks
        lastStrafe = strafeTicks
    }

    fun update(leftTicks: Int, rightTicks: Int, strafeTicks: Int) {
        val dL = (leftTicks   - lastLeft)   / ticksPerMm
        val dR = (rightTicks  - lastRight)  / ticksPerMm
        val dS = (strafeTicks - lastStrafe) / ticksPerMm
        lastLeft   = leftTicks
        lastRight  = rightTicks
        lastStrafe = strafeTicks

        val dTheta   = (dR - dL) / (2.0 * halfTrackMm)
        val dForward = (dL + dR) / 2.0
        val dLateral = dS - lateralOffsetMm * dTheta   // remove arc artifact

        val phi = theta + dTheta / 2.0   // arc midpoint heading

        x     += dForward * cos(phi) - dLateral * sin(phi)
        y     += dForward * sin(phi) + dLateral * cos(phi)
        theta += dTheta
    }
}
```

## GoBUILDA Pinpoint

The [GoBUILDA Pinpoint]([https://www.gobilda.com/pinpoint-odometry-computer/](https://www.gobilda.com/pinpoint-v2-odometry-computer-imu-sensor-fusion-for-2-wheel-odometry/)) is a dedicated co-processor that connects directly to two odometry pods (typically GoBUILDA's dead wheel pods) and communicates over I²C with the Control Hub. It handles all of the odometry math on-chip and exposes a ready-to-use pose directly to your OpMode.
### What It Does Differently

Rather than running odometry in your 20–30 ms loop, the Pinpoint samples its encoders at a much higher rate internally. The pose you read from it over I²C reflects the most recently computed estimate, effectively decoupling odometry accuracy from your loop timing. This matters most at high speed: a robot travelling at 1 m/s covers 20–30 mm per loop causes coarse heading changes. The Pinpoint's internal loop is substantially faster.

The device also exposes its internal velocity estimate, which can be fed directly into the derivative term of a [[PID Controllers]] without computing a finite difference yourself.

### Coordinate Convention

The Pinpoint uses a right-handed coordinate system. When you mount the device, you specify its orientation relative to the robot chassis (which port is forward, which is left) and the encoder resolutions. After that, the returned pose is already in **field-centric** coordinates once you set the starting pose.
$$
\mathbf{q}_\text{pinpoint} = \begin{pmatrix} x \\ y \\ \theta \end{pmatrix} \in \mathbb{R}^3
$$
​​
$z$ is still tracked separately (e.g. a lift encoder on the Control Hub) and combined into the full $\mathbb{R}^4$ pose.
### Mounting Geometry

The Pinpoint expects you to supply the **X offset** and **Y offset** of each encoder pod relative to the robot's center of rotation, in millimetres. Getting this measurement right is the single most important tuning step — an incorrect offset produces the same arc artifact described in the dead-wheel section.

<video autoplay muted playsinline controls>  
<source src="/static/concepts/odometry/PinpointMount.webm" type="video/webm">  
</video>

In Kotlin you can use the vendored GoBuilda Pinpoint SDK:
```kotlin
import com.qualcomm.robotcore.eventloop.opmode.LinearOpMode
import com.qualcomm.robotcore.eventloop.opmode.TeleOp
import org.firstinspires.ftc.teamcode.GoBildaPinpointDriver      
import org.firstinspires.ftc.teamcode.GoBildaPinpointDriver.EncoderDirection
import org.firstinspires.ftc.teamcode.GoBildaPinpointDriver.GoBildaOdometryPods

@TeleOp(name = "Pinpoint Odometry Demo")
class PinpointOdometryOpMode : LinearOpMode() {

    override fun runOpMode() {
        val odometry = hardwareMap.get(GoBildaPinpointDriver::class.java, "pinpoint")

        // Physical offsets of the two encoder pods from the robot's center of rotation.
        // Measure these carefully
        odometry.setOffsets(
	        -84.0,
	        168.0,
        )

        // Pod type sets the encoder resolution automatically
        odometry.setEncoderResolution(GoBildaOdometryPods.goBILDA_4_BAR_POD)

        odometry.setEncoderDirections(
            EncoderDirection.FORWARD,
            EncoderDirection.FORWARD,
        )

        odometry.resetPosAndIMU()

        waitForStart()

        while (opModeIsActive()) {
            odometry.update()

            val pose     = odometry.position         
            val velocity = odometry.velocity          

            val x     = pose.getX(DistanceUnit.MM)
            val y     = pose.getY(DistanceUnit.MM)
            val theta = pose.getHeading(AngleUnit.RADIANS)

            // Combine with a lift encoder to form the full R^4 pose
            val z = liftMotor.currentPosition / LIFT_TICKS_PER_MM

            telemetry.addData("x (mm)",    "%.1f".format(x))
            telemetry.addData("y (mm)",    "%.1f".format(y))
            telemetry.addData("z (mm)",    "%.1f".format(z))
            telemetry.addData("θ (deg)",   "%.2f".format(Math.toDegrees(theta)))
            telemetry.addData("vX (mm/s)", "%.1f".format(velocity.getX(DistanceUnit.MM)))
            telemetry.update()
        }
    }
}
```

### Using Pinpoint Velocity with a PID Controller

Because the Pinpoint exposes velocity directly, you can use it as the [[PID Controllers#The Derivative Term (D)|derivative measurement in a PID controller]] instead of differencing consecutive positions. This eliminates the finite-difference noise problem:

$$
u(t)=K_P​e(t) + K_I​ \int_{0}^{t}e(\tau)d\tau + K_D ​\underbrace{v_{measured}​(t)}_{pinpoint}​
$$


```kotlin
/**
 * Velocity-augmented PID using Pinpoint's direct velocity output.
 * This avoids the noisy finite-difference derivative of standard PID.
 */
fun calculateWithVelocity(
    targetMm:    Double,
    measuredMm:  Double,
    velocityMms: Double,
): Double {
    val dt    = timer.seconds().also { timer.reset() }
    val error = targetMm - measuredMm

    integralSum = (integralSum + error * dt).coerceIn(-integralMax, integralMax)

    // D term uses measured velocity directly
    val output = kP * error + kI * integralSum - kD * velocityMms
    return output.coerceIn(-outputMax, outputMax)
}
```

> Note the **negative sign** on the velocity term: velocity is positive when the robot 
> moves toward increasing position, which *reduces* error. Using $−K_Dv$ is equivalent 
> to $+K_D \frac{de}{dt}$​ when the target is stationary, because
>  $\frac{de}{dt} = \frac{d}{dt}(P_D - P_t) = -\dot{P}_t = -v$ 

## Comparison

| Method                | Slip Immune | Strafe Tracking  | Setup Complexity | Accuracy |
| --------------------- | ----------- | ---------------- | ---------------- | -------- |
| Drive encoders        | ✗           | ✗ (mecanum only) | Low              | Low      |
| Dead wheels (3-wheel) | ✓           | ✓                | Medium           | High     |
| GoBUILDA Pinpoint     | ✓           | ✓                | Low–Medium       | High     |

For most FTC teams, the GoBUILDA Pinpoint is the fastest path to reliable field-centric pose tracking. If you are building a custom chassis without a commercial pod solution, three-wheel dead wheels give equivalent accuracy at the cost of more mechanical and software setup. Drive encoder odometry is a reasonable fallback for prototyping but should not be used in competition autonomous routines where positional accuracy matters.

---

## Combining Odometry with PID

Odometry provides the $P_t$​ measurement; the PID controller turns the error $e(t)=P_D − P_t$ ​ into a motor command. The two systems form a closed feedback loop:

$$
\underbrace{\mathbf{q}_\text{target}}_{\text{path planner}} \xrightarrow{\;e(t)\;} \underbrace{u(t)}_{\text{PID}} \xrightarrow{\;\text{motors}\;} \underbrace{\mathbf{q}_\text{measured}}_{\text{odometry}} \longrightarrow e(t)
$$

With a full $(x, y, \theta)$ pose estimate, you can run three independent PID loops simultaneously — one for $x$, one for $y$, one for $\theta$ — and project the outputs back onto the robot's local frame to compute individual wheel powers. This is the foundation of **field-centric drive** and **autonomous trajectory following**.

