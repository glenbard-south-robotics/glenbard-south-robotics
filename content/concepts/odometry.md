---
title: Odometry
tags:
  - concepts
---
Odometry is the process of estimating a robot's **pose** — its position and orientation in space by integrating sensor readings over time. Rather than relying on where you _told_ the robot to go, odometry tracks where it _actually went_. This distinction matters enormously in FTC: wheels slip, tiles compresses unevenly, and motors don't respond identically. Without odometry, positional error accumulates. With it, you can feed corrective signals back into a PID controller and close the loop.

---

# The Pose Vector $\mathbf{q}$

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

# Drive Encoders

![[UltraplanetaryMotorREV.png]]



 