# **GR00T-Ready**


# INTRODUCTION

## Purpose

To create a standardized and repeatable framework for assessing whether robot platforms and partners are ready for GR00T integration. It establishes a consistent technical baseline across all tiers (Official and Self-Serve), de-risks development through early feasibility validation, and gates official partnership on both technical and non-commercial readiness across all robot platforms.

## Scope

This evaluation framework defines standardized bring-up and validation procedures for general-purpose humanoid robotics platforms. It encompasses technical baselines (whole-body motion control, sensor and actuator fidelity, embedded compute, middleware compatibility, end-effector manipulation, teleoperation, simulation readiness, security, and OTA capability), tiered engagement models (Official certification vs. Self-Serve adoption), and non-technical readiness (commercial accessibility, supply-chain scalability, compliance posture, support infrastructure, and developer documentation).

## Assumptions

* Robots are available with SDK access.  
* Thor is flashed with JetPack and successfully boots to the system with all JetPack libraries running, including CUDA-X.  
* Robot firmware must be compatible with ROS2 controllers.

# SUPPORT TIER DEFINITIONS

Service levels that determine technical baseline targets. Tiers do NOT relax admission criteria.

## Tier 1: Official

Partners that have completed the full GR00T-Ready evaluation and meet all qualification criteria to become an official GR00T platform partner candidate.

### Official Partner Benefits

* **NVIDIA engineering support:** Dedicated technical engagement, priority bug escalation, and roadmap alignment.  
* **Certification maintenance:** Subject to periodic re-evaluation to ensure continued compliance with evolving GR00T baselines.  
* **Joint go-to-market:** Eligible for official GR00T Platform Partner designation, developer ecosystem access, and joint marketing collateral.

## Tier 2: Self-Serve

For organizations adopting GR00T components without pursuing official partner certification.

* **Self-administered evaluation:** Use the open technical evaluation framework to independently assess hardware and software compatibility against GR00T baselines.  
* **Flexible adoption path:** Integrate any subset of the platform (Isaac Sim, Isaac ROS, GR00T models, etc.) as needed, without requiring full-stack certification.  
* **No official certification commitment:** Participation in this tier does not imply NVIDIA endorsement or official GR00T Platform Partner status.  
* **Limited NVIDIA engagement:** NVIDIA may provide general guidance, documentation, ecosystem resources, or selective technical feedback, but dedicated engineering support, priority escalation, and roadmap alignment are reserved for Tier 1 partners.  
* **No admission enforcement:** Commercial criteria (manufacturing scale, global availability, support infrastructure) are not gates for Self-Serve access.

## Tier Selection Impact

Tiers determine the service level and partner designation, not the technical baseline.

* **Evaluation scope:** The same technical baselines apply regardless of tier. Selecting Self-Serve does not lower the technical bar; it simply means the partner is not pursuing formal certification or NVIDIA-backed support at this time.  
* **Admission criteria:** Official tier requires passing the full evaluation, including commercial and operational readiness. Self-Serve relies on technical self-assessment without formal validation of commercial admission criteria.  
* **Engagement model:** Tiers do not relax admission criteria. A Self-Serve partner is not partially certified; they are un-certified but enabled. The evaluation framework remains the authoritative gate for Official status.

# PLATFORM ADMISSION CRITERIA

## TECHNICAL EVALUATION

The **Must-Have** column marks items that are mandatory for Official
certification. Each entry states the minimum score the item must reach (e.g.
`1 = Must-Have`) and why it is required (safety / table stakes / critical). A
must-have item scoring below its stated level blocks certification regardless of
the overall total. Items with a blank Must-Have cell are scored and contribute to
the total, but are not on their own gating.

The **Evidence** column and non-technical Evidence sections list the artifacts
required to document evaluation results and support the assigned score, matching
the `evidence` fields in `criteria/criteria.yaml`.

### Hardware

| Items | Method / Metric | Success criteria<br>0 \= No support<br>1 \= Partial support<br>2 \= Fully support | Must-Have | Evidence |
| ----- | ----- | ----- | --------- | ----- |
| **System Integrity** |  |  |  |  |
| Emergency Stop (E-stop) | Dual-redundancy confirmed | 1 \= Only on robot stop or only on-remote controller stop 2 \= All support | 1 = Must-Have (safety) | Video of both stop paths + wiring diagram. Optional additional evidence: functional-safety assessment or certification documentation identifying the applicable standard, claimed level, and covered E-stop function |
| Port Functionality (USB, Ethernet) | Operational integrity confirmed: exercise every external port and measure sustained throughput per port type | 1 \= All ports functional 2 \= All ports functional and each sustains at least its class rate (1 GbE class for Ethernet, USB 3.x class or better for USB) | 1 = Must-Have (table stakes) | Port inventory + per-port throughput log |
| Integrated Audio (Mic & Speaker) | Confirm functionality | 1 \= Only speaker 2 \= All support |  | Captured microphone samples + audio or video recording of speaker output |
| Debug Mode Connectivity | Confirm successful connection | 1 \= Support to debug partial devices on the robot including head cameras, robot joints, wrist cameras, IMUs and other necessary sensors<br>2 \= Support to debug all devices on the robot | 1 = Must-Have (critical) | Debug session log listing every reachable device |
| Remote/App Control | Confirm functionality | 1 \= Support only remote or App<br>2 \= All support |  | Demo video of each control path |
| Power Supply Output | Verify against manufacturer specs (voltage, current, and power) | 1 \= Minimum power supply for all peripherals on the robot running on normal mode 2 \= Maximum power supply for all peripherals on the robot running on max mode | 1 = Must-Have (safety) | PSU datasheet + measured V/I/P in both modes |
| **Onboard Compute** |  |  |  |  |
| Full software stack is verified with the correct JetPack release, successful boot, and all required libraries available. | Verify the JetPack release, confirm the system boots to a normal operational state, and validate that all required libraries are installed and load correct | 1 \= Previous JetPack version  2 \= Latest JetPack version |  | L4T release output (`cat /etc/nv_tegra_release`) + corresponding JetPack version + current-boot journal (`sudo journalctl -b 0 --no-pager`) + library check |
| Validate operational stability and throughput of the Thor platform. | Max stability / throughput: sustained fp16 GEMM and memory-bandwidth benchmarks in the platform's max sustained power mode, compared against the Jetson Thor reference result for the same benchmark (not marketing peak figures) | 2 \= At least 85% of the reference benchmark result, stable within ±5% across the run |  | Benchmark report vs Thor spec sheet |
| Conduct an endurance stability check | Continuous stability in the platform's maximum sustained power mode (MAXN or the vendor-named equivalent); record the mode used | 1 \= More than 3 hours in the maximum sustained power mode |  | Continuous tegrastats log (`sudo tegrastats --interval 1000 --logfile <output-file>`) |
| Verify sustained CPU and GPU clock speed stability under inference load | No throttling under inference load in the platform's maximum sustained power mode (MAXN or the vendor-named equivalent); record the mode used | 2 \= No throttling or overcurrent warning |  | tegrastats log during inference load + kernel journal (`sudo journalctl -k -b 0 --no-pager`) covering the test interval + recorded workload and power-mode configuration |
| Verify RAM capacity is sufficient | Capacity verified to be at least that of Jetson Thor | 0 \= Less than 128 GB 2 \= 128 GB or more |  | System memory report (`free -b`), including the Mem total in bytes |
| Verify NvME storage capacity and throughput | Formatting EXT4 successfully on NvME storage(\>1TB). Stress test runs for \> 4 hours with no failures | 1 \= Format on \>1TB storage.  2 \= Stress test \> 4 hours. |  | Filesystem type and capacity output (`lsblk -b -o NAME,SIZE,FSTYPE,MOUNTPOINTS`) + fio stress-test report, including job configuration and runtime |
| Check for PTP (Precision Time Protocol) | PTP stability verified | 1 \= Less than 100 us time offset 2 \= Less than 10 us time offset |  | ptp4l /phc2sys offset log |
| Verify all expected hardware modules (Wi-Fi, Bluetooth, QSFP) are enabled and functioning | All fitted modules verified enabled and functioning; modules not fitted are excluded and named in the result note | 1 \= Some fitted modules functional 2 \= All fitted modules functional |  | Wi-Fi status (`nmcli device status`, `iw dev`) + Bluetooth controller status (`bluetoothctl list`, `bluetoothctl show`) + fitted QSFP interface/link status (`ethtool <interface>`) and transceiver information (`ethtool -m <interface>`, where supported); identify modules not fitted |
| **Sensor** |  |  |  |  |
| Confirm available USB ports are adequate for all peripherals | Verify the data transfer of every USB port and compare the usable count against the peripherals the platform requires; record both numbers | 1 \= Enough usable ports for all required peripherals 2 \= Enough usable ports for all required peripherals with spare capacity |  | Vendor physical port map + required-peripheral list + USB topology output (`lsusb -t`) with peripherals connected |
| Evaluate USB bandwidth and data transfer stability | Max throughput, zero dropouts under load | 1 \= Support bandwidth more than 1 Gbps 2 \= Support bandwidth more than 5Gbps |  | Vendor per-port bandwidth specifications + USB topology and negotiated link speeds (`lsusb -t`) |
| Verify head camera operational stability and resolution | Long time stability at max resolution | 1 \= More than 1 hour 2 \= More than 4 hours | 1 = Must-Have (critical) | Continuous stream (bag) + frame-drop stats |
| Confirm head camera angle adjustments provide optimal FoV for manipulation | Set positions for head joints and check the FoV of camera | 1 \= Can set head position and joints 2 \= FoV can see arm and hands | 1 = Must-Have (critical) | Vendor FoV specifications + sample frames at commanded head positions |
| **Actuator** |  |  |  |  |
| Read and Command Joint States | Compare the values | 1 \= Greater than 250 Hz control frequency 2 \= Greater than 1000 Hz control frequence | 1 = Must-Have (critical) | Datasheet specifications for supported control types + timestamped joint-state capture (bag) |
| Verify joint angle range limitations against manufacturer specs | Verify limits against manufacturer specs | 1 \= Error within 5% 2 \= Error within 1% |  | Measured range table vs datasheet |
| Evaluate PD controller precision and responsiveness | Commanded step response at the vendor's recommended gains; record step size and gain configuration. Measure settling time, absolute steady-state error and overshoot | 1 \= No overshoot, settles within ±5% of the step in under 300 ms, absolute steady-state error under 2° 2 \= No overshoot, settles within ±1% of the step in under 100 ms, absolute steady-state error under 0.5° |  | Step-response capture (bag) + plots + table of settling time, overshoot, and steady-state error |
| Assess single-arm and dual-arm payload limits | Verify max payload against specs | 1 \= Single arm match 2 \= All match | 1 = Must-Have (safety) | Load-test video + measured table vs payload datasheet specs |
| **Network** |  |  |  |  |
| Verify sufficient network bandwidth for all sensor streams | Sustained bidirectional throughput test on each fitted interface. Level 2 applies only where a 10 GbE-or-faster interface is fitted; on 1 GbE-only platforms level 1 is the maximum attainable and the note must record the fitment | 1 \= Sustains at least 1 GbE class measured 2 \= Sustains at least 10 Gb/s on a fitted 10 GbE-or-faster interface |  | Throughput results with all streams active |
| Able to connect to Ethernet | Verify with lab Ethernet, speedtest-cli reports \> 30M | 1 \= Able to connect 2 \= Throughput pass |  | speedtest-cli output |
| Able to connect to Wi-Fi | Verify with lab Wi-Fi, speedtest-cli reports \> 30M | 1 \= Able to connect 2 \= Throughput pass |  | speedtest-cli output |
| **Dexterous Hands Basic** |  |  |  |  |
| Verify full operational range and articulation of all joints | Verify full operational range against specs for each independently-actuated joint, in absolute joint units. Coupled/underactuated joints are enumerated in the note and assessed for presence of motion only | 1 \= All independently-actuated joints within 5% of specified range 2 \= All independently-actuated joints within 1% of specified range |  | Joint sweep capture (bag) vs spec table |
| Verify maximum grasping force/torque and payload limits | Verify max limits against specs | 1 \= Only payload match 2 \= All match |  | Force-gauge measurements + grasp video |
| Verify the functionality of the hand's various control modes and configurations | Verify every supported mode and config | 1 \= Support program control 2 \= All support |  | Per-mode test log |
| Verify tactile sensor resolution/operating frequency/contact info against the specs | Verify max resolution / frequency against specs, using the spatial branch matching the sensor class (taxel pitch for taxel arrays, image resolution + FPS for vision-based); record which branch was used | 1 \= At least 30 Hz, 1 cm taxel pitch or contact features resolved at 1 cm or better, and 0.1 N load sensitivity 2 \= At least 180 Hz, 1 mm taxel pitch or contact features resolved at 1 mm or better, and 0.005 N load sensitivity |  | Datasheet + measured readings (bag) |

### Software

| Item | Method / Metric | Success criteria<br>0 \= No support<br>1 \= Partial support<br>2 \= Fully support | Must-Have | Evidence |
| ----- | ----- | ----- | --------- | ----- |
| **Operating System (OS)** |  |  |  |  |
| Verify successful installation of all required system and application packages | Verify all packages and their dependencies install and load: Isaac ROS, Isaac Teleop, GR00T, and [LEAPP](https://github.com/nvidia-isaac/leapp) (Lightweight Export Annotations for Policy Pipelines — requires Python 3.10+ and PyTorch 2.6+; verify with `python -c "import leapp"`) | 2 \= All support | 2 = Must-Have (table stakes) | Install log |
| Confirm successful build and deployment of the reference application/policy | Replay trajectories with ROS2 controller | 2 \= Replay match benchmark positions |  | Build log + replay trace (bag) + error plot |
| Validate storage throughput (IOPS) for real-time data logging | Max IOPS meets needs for all concurrent streams | 1 \= More than 100Mb/s 2 \= More than 1000Mb/s |  | IOPS results while all streams record |
| Verify that the system's SM number is correctly reported | Verify SM reporting | 2 \= All match |  | deviceQuery /system report |
| **Software Development Kit (SDK)** |  |  |  |  |
| IMU (Inertial Measurement Unit) |  |  |  |  |
| Verify synchronized time and data streams | Test synchronized time against a timestamp source whose resolution is finer than the level being assessed; record the source and its resolution. Where the timestamp is quantized at or above a level's threshold, that level cannot be assessed and the next lower level is the maximum attainable | 1 \= Less than 1ms jitter 2 \= Less than 0.1ms jitter, measured against a sub-0.1 ms timestamp source | 1 = Must-Have (critical for WBC) | Synchronized capture (bag) + jitter histogram |
| Verify stability and low-noise characteristics | Verify max stability / low noise | 1 \= Gyro noise 0.1 °/s/√Hz and accel noise 0.01 m/s²  2 \= Gyro noise 0.01 °/s/√Hz and accel noise 0.003 m/s²  |  | Static capture (bag) + Allan-variance plot |
| Evaluate time synchronization accuracy/jitter to main control loop | Verify max accuracy, minimal jitter | 2 \= All match |  | Alignment measurement (bag) |
| Check for and correct intrinsic errors (bias, scale factor, etc.) | Verify max tolerance compliance | 2 \= All match |  | Calibration report |
| Verify stability over time (zero-drift/bias gradient) | Robot at rest ≥ 1 hour; measure worst-axis fused-attitude (rpy) drift | 1 \= More than 1 hour with attitude drift under 1 °/h 2 \= More than 1 hour with attitude drift under 0.5 °/h |  | ≥1 h static drift capture (bag) |
| Verify IMU output frequency | Verify IMU output frequency and stability at an on-robot subscriber, so transport losses off the robot are excluded. Where no vendor rate is published, record that and assess against level 1 only | 1 \= More than 100 Hz 2 \= Meets the vendor-specified rate with stable output and under 0.1% sample loss measured on-robot |  | Rate capture (bag) + loss count |
| Force/Torque (F/T) Sensors |  |  |  |  |
| \[if have\] Verify stable and low-noise force and torque readings (6-DOF) | Verify max stability / low noise | 1 \= Error within 1% 2 \= Error within 0.1% |  | Known-load captures (bag) + error calc |
| \[if have\] Check for zero-drift when the sensor is unloaded | Verify zero-drift | 1 \= Error within 0.5% full scale 2 \= Error within 0.1% full scale |  | Unloaded drift capture (bag) |
| \[if have\] Verify the sensor's response linearity by applying precisely known loads | Verify Max linearity | 2 \= All match |  | Calibration curve |
| \[if have\] Verify F/T sensor data output frequency | Test the frequency of data output | 2 \= More than 1000Hz |  | Rate capture (bag) |
| Tactile Sensors |  |  |  |  |
| Verify all individual taxels report data correctly | Verify all taxels functional | 1 \= All taxels report, with up to 5% degraded but calibratable 2 \= All taxels report correctly |  | Taxel map readout (bag), per-taxel pass/fail |
| Verify sensor responsiveness and force-reading linearity | Verify max linearity and responsiveness | 1 \= Monotonic and responsive, within twice the specified linearity tolerance 2 \= Meets the specified linearity and responsiveness figures |  | Probe test data (bag) |
| Assess persistence and noise characteristics | Verify max stability / low noise | 1 \= Stable readings with residual noise correctable by calibration 2 \= Meets the specified stability and noise figures without correction |  | Idle capture (bag) + persistence log |
| \[if have\] Verify data stream bandwidth for vision-based tactile sensor image output | Verify max resolution / FPS supported against the specs | 1 \= Stream available at reduced resolution or FPS, or without a raw-image path 2 \= Full specified resolution and FPS available, raw-image path included |  | Resolution /FPS /bandwidth trace |
| \[if have\] Verify capability to deactivate vision-based tactile sensors for bandwidth reduction | Verify deactivation feature | 1 \= Deactivation possible but without a documented or runtime-accessible API 2 \= Supported through a documented runtime API |  | Before/after bandwidth log |
| \[if have\] Verify tactile data stream refresh rate | Test refresh rate sustained at the host; record the vendor's rated maximum rate for comparison | 1 \= At least 150 Hz sustained 2 \= Above 200 Hz, or sustains the vendor's rated maximum where that maximum is 200 Hz or lower |  | Rate capture (bag) |
| Cameras |  |  |  |  |
| Verify functional integrity of all camera streams (color, depth) | Verify all streams fully functional | 1 \= Head cameras supported 2 \= All support | 1 = Must-Have (critical) | Sample recordings (bag) of every stream |
| Camera Calibration | Verify camera calibration parameters and calibration quality. | 1 \= Calibration data provided 2 \= Calibration verified and passes accuracy validation |  | Intrinsics/extrinsics files + reprojection-error report |
| Multi-Camera Time Synchronization | Verify all camera streams use a common time source (PTP/system clock/hardware sync) and validate synchronization accuracy. | 1 \= Common timestamp source available 2 \= Synchronization verified, max timestamp difference \< 1 ms |  | Multi-camera capture (bag) + timestamp-diff analysis |
| Camera Color Reproduction and Consistency | Verify color accuracy, white balance stability, and color consistency under different lighting conditions (e.g., daylight, warm indoor light, cool white LED, low-light environment). Compare captured images against reference color targets and check for abnormal color casts, oversaturation, or color shifts. | 1 \= Minor color deviation under some lighting conditions, but image remains usable. 2 \= Natural and consistent color reproduction across all tested lighting conditions with no abnormal color casts or significant color shifts. |  | Images vs color target in 4 lighting conditions |
| Supported Resolution and Frame Rate | Verify camera resolution, frame rate, and stream stability. | 1 \= Camera specifications provided 2 \= Resolution and FPS verified against specifications with stable streaming |  | Spec sheet + measured capture (bag) |
| Stereo and Wrist Camera FoV Coverage | Verify stereo and wrist cameras provide wide-angle coverage of the manipulation workspace, including hands, tools, and nearby objects. | 1 \= Workspace coverage acceptable but with noticeable blind spots or occlusions 2 \= Wide FoV validated with full manipulation workspace coverage and minimal occlusion | 1 = Must-Have (table stakes) | Coverage images showing hands, tools, objects |
| Temperature Sensors (Thermal Management) |  |  |  |  |
| Verify active and accurate temperature data streams | Verify accurate real-time readings | 2 \= Error within 1 |  | Temperature readings from tegrastats + photo showing the IR thermometer reading while pointed at the measured component |
| Ensure logged temperature readings remain within operating range during stress tests | Verify operating range compliance | 2 \= All match |  | Stress-test temperature traces (bag) |
| Verify the system triggers a clear overheating warning when a joint is in abnormal mode | Verify warning system | 2 \= All support |  | Induced-fault test log/video |
| Verify the data refresh rate for temperature readings | Verify the refresh rate frequency | 2 \= More than 10Hz |  | Rate capture (bag) |
| **Whole Body Control (WBC)** |  |  |  |  |
| Verify the existence and stability of WBC policy with all peripherals. | Verify WBC under max load | 2 \= All support | 2 = Must-Have (safety) | Policy description + max-load video + telemetry (bag) |
| Fixed-Base Manipulation Stability (initial posture) | Verify continuous balance | 1 \= More than 1 hour 2 \= More than 3 hours |  | Continuous run video + telemetry (bag) |
| Stability during upper-body manipulation tasks | Verify continuous balance | 1 \= More than 1 hour 2 \= More than 3 hours |  | Continuous run video + telemetry (bag) |
| Locomotion Stability (walking with all peripherals) | Verify continuous balance | 1 \= More than 1 hour 2 \= More than 3 hours | 1 = Must-Have (critical) | Continuous walking video + telemetry (bag) |
| Locomanipulation Stability (walking with max payload) | Verify continuous balance with max payload | 1 \= More than 1 hour 2 \= More than 3 hours | 1 = Must-Have (critical) | Continuous walking video + telemetry (bag) |
| Verify independent control functionality for the upper body. | Verify Independent control | 1 \= Arm \+ head control 2 \= Arm \+ head \+ waist control |  | Command/response demo video |
| **Teleoperation** |  |  |  |  |
| Evaluate precision and reliability of the retargeter system | Verify max precision and reliability | 2 \= All match | 2 = Must-Have (critical) | Commanded vs achieved poses (bag), repeated trials |
| Verify end-to-end functionality for glove-based Teleop | Verify max accuracy / consistency | 2 \= All match with no pause or jitter |  | Session recording (bag + video) + packet transmission and reception timing jitter logs + end-effector tracking error measurements |
| Verify existence and functionality of a user calibration utility for gloves | Verify max calibration fidelity | 2 \= All support |  | Utility walkthrough + calibration file |
| Verify functionality, responsiveness, and operating range of the haptic feedback system | Verify full range haptic | 2 \= All match |  | Response test log across range |
| Verify end-to-end functionality for hand-tracking based Teleop | Verify max accuracy / consistency | 2 \= All match with no pause or jitter |  | Session recording (bag + video) + packet transmission and reception timing jitter logs + end-effector tracking error measurements |
| Measure end-to-end latency of the teleoperation pipeline | Test latency from operator input capture to commanded robot motion, timestamped at both ends. Where only the robot-side segment can be instrumented, record that scope with the result | 1 \= Less than 50ms P99 latency 2 \= Less than 20ms P99 latency |  | Timestamp trace (bag) with P99 |
| **Simulation** |  |  |  |  |
| Robot Model Verification |  |  |  |  |
| Verify kinematic and dynamic properties in the asset file align with physical robot specs | Verify fidelity alignment by system identification: excite the physical robot across its joints, identify the dynamic parameters (link masses, inertias, joint friction, torque constants) from the measured response, and compare against the values declared in the asset. Kinematics compared against the manufacturer's specification | 1 \= Only PhysX match 2 \= All match | 1 = Must-Have (table stakes) | Asset files (URDF/USD/MJCF) + AnchorLab report |
| Check that the visual model (meshes) is correctly linked and displayed | Verify the visual integrity | 2 \= All support |  | Rendered screenshots |
| Validate the home/initial posture configuration | Verify posture | 2 \= All match |  | Config file + sim vs physical pose |
| Isaac Sim Compatibility |  |  |  |  |
| Verify assets load correctly in Isaac Sim without errors/warnings | Verify error-free loading | 2 \= All support |  | Load log |
| Check that the PhysX engine accurately simulates rigid body interactions | Verify physics fidelity against system identification results from the physical robot: replay an identical joint trajectory in PhysX and on the robot, and compare joint states and contact behaviour | 2 \= All match |  | PhysX-vs-hardware report |
| Check that the Newton engine accurately simulates rigid body interactions | Verify physics fidelity against system identification results from the physical robot: replay an identical joint trajectory in Newton and on the robot, and compare joint states and contact behaviour | 2 \= All match |  | Newton-vs-hardware report |
| Confirm asset supports necessary communication interfaces (UCX server) | Verify UCX / Comms. UCX \= [Unified Communication X](https://docs.nvidia.com/multi-node-nvlink-systems/multi-node-tuning-guide/ucx.html), NVIDIA's core communications library (get/put, send/receive, active messages between CPU/GPU endpoints). The asset exposes a UCX endpoint an external client connects to: confirm the UCX stack and transports are present (`ucx_info -d`, `UCX_TLS`), then close a command-in / status-out loop over it — client commands drive the asset and joint state is returned to the client | 2 \= All support |  | Connection test log |
| Verify stability and determinism of robot's motion control in Isaac Sim | Verify stability / determinism | 2 \= All support |  | Repeated-run trajectory diff |
| MuJoCo Compatibility |  |  |  |  |
| Verify assets load correctly in the MuJoCo simulator | Verify error-free loading | 2 \= All support |  | Load log |
| Check that the physics engine accurately simulates rigid body interactions | Verify physics fidelity in two parts. Structural: DoF count, link masses and inertias against the source URDF/USD. Dynamic: replay an identical joint trajectory in MuJoCo and on the physical robot and compare joint states. Record which parts were run | 1 \= Structural properties match within 1% and simulation is deterministic 2 \= Structural match plus replayed trajectories tracking the physical robot within 5% RMSE per joint |  | Sim-vs-hardware comparison |
| Validate the stability of simple control tasks (standing/hovering) within MuJoCo | Verify control stability | 2 \= All match |  | Run log |
| **Security** |  |  |  |  |
| Platform Boot Security |  |  |  |  |
| Secure Boot. Validate Secure Boot is enabled on the Jetson platform | System boots only authenticated bootloader, kernel, and firmware images | 0 \=  Secure Boot not enabled 1 \= Secure Boot enabled but not validated across the full boot chain. 2 \= Secure Boot enabled and full boot chain validation passes | 1 = Must-Have (critical) | Fuse/status output + boot-chain validation report |
| Rollback Protection. Verify system cannot boot an older unauthorized release. | Attempt to install or boot an older bootloader, kernel, or system image. | 0 \= Older image can boot. 1 \= Rollback is partially blocked but not consistently enforced 2 \= Rollback protection is enforced for protected boot component |  | Downgrade-attempt log |
| Key and Data Protection |  |  |  |  |
| Secure Storage. Verify key material and sensitive platform data are stored in secure storage. | Keys, certificates, and sensitive configuration are not stored as plain files on the rootfs. | 0 \= Keys stored in plain files. 1 \= Some keys use protected storage 2 \= Required keys use secure storage or TEE backed storage. |  | Architecture doc + rootfs audit |
| Disk Encryption. Verify rootfs or sensitive data partition encryption. | Data at rest is protected using disk encryption for required partitions | 0 \= No disk encryption. 1 \= Only selected data folder or partition is encrypted 2 \= Required rootfs or data partitions are encrypted and unlock correctly during b |  | Partition status + unlock demonstration |
| Platform Hardening and Access |  |  |  |  |
| Default Account and Debug Lockdown. Verify production image has no default passwords, open debug ports, or unrestricted root access. | Production image blocks default credentials and unnecessary debug access | 0 \= Default passwords or unrestricted debug access exist 1 \= Some accounts or debug interfaces are restricted 2 \= No default passwords, debug access is locked down, and admin access is controlled |  | Hardening audit: accounts, port scan, root policy |
| Security Logging. Verify security relevant events are logged | Login attempts, admin actions, Secure Boot status, OTA security | 0 \= No security logs. 1 \= Basic logs only 2 \= Required security events are logged and retained for debugging and audit |  | Log extract + retention policy |
| **Over-the-Air (OTA) Update** |  |  |  |  |
| Platform OTA Capability |  |  |  |  |
| Image based OTA. Validate OTA update without manual reflash | Robot can update JetPack, BSP, bootloader, kernel, rootfs, and system packages through OTA | 0 \= No OTA support  1 \= Partial support.  2 \= Full image based OTA supported |  | OTA session log, versions before/after |
| Rootfs A/B and recovery. Test OTA with rootfs A/B and interrupted update | System can boot into updated slot or recover safely | 0 \= OTA failure may brick device 1 \= Manual recovery required 2 \= Recovery flow verified |  | Interrupted-update test log |
| Secure and Controlled Update |  |  |  |  |
| Secure Boot compatibility. Validate OTA with Secure Boot enabled. | Updated system boots only authenticated code. | 0 \= Not supported. 2 \= Works with Secure Boot enabled |  | Post-OTA boot log |
| Secure OTA payload. Verify payload signing, validation, and encryption | OTA payload is authenticated before installation. | 0 \= No payload security. 2 \= Signature validation and encryption supported |  | Design doc + validation log |
| OTA Operations and Validation |  |  |  |  |
| OTA logging. Verify OTA logs and audit records  | Version, payload ID, result, trigger source, and failure reason are retained | 0 \= No logs 1 \= Failure logs only  2 \= Full audit logs retained |  | Audit log sample |
| Post update validation.Run smoke test after OTA reboot  | JetPack, CUDA, TensorRT, Isaac ROS, cameras, network, and robot SDK pass validation | 0 \= No validation  1 \= Boot check only 2 \= Full smoke test passes |  | Smoke-test report covering all components |

## NON-TECHNICAL EVALUATION

This section applies exclusively to Tier 1: Official partners. All gates below must be fully satisfied to achieve Official certification. Tier 2: Self-Serve partners are not required to meet these non-technical criteria; they may proceed with technical self-assessment and modular adoption regardless of commercial readiness, supply-chain scale, or support infrastructure.

### General Commercial Accessibility

#### Requirement

* **Developer-ready distribution:** Will sell to developers with a viable commercial model and accessible procurement path.  
* **Regional or global availability:** Regionally or globally available to serve the developer and deployment ecosystem.

#### Methodology

* Review pricing model, sales channels, and procurement workflow.  
* Verify shipping coverage, regional entity presence, and localization.

#### Measurement

* Published developer-kit pricing and accessible procurement path (e-commerce, distributor, or direct).  
* Regional or global availability with local-language support and in-country warranty service.

#### Evidence

Published pricing + procurement instructions + regional shipping, language-support, and warranty coverage

### Supply-Chain

#### Requirement

Can manufacture at scale, including provision of replacement parts and sustained supply chain.

#### Methodology

* Review production capacity plans and facility certifications.  
* Audit supplier agreements and second-source coverage for critical components.  
* Verify replacement-parts inventory strategy and fulfillment process.

#### Measurement

* Documented monthly production capacity and ramp curves.  
* Replacement parts availability commitment.  
* Sustained supply chain with qualified, diversified suppliers.

#### Evidence

Monthly capacity and ramp plan + qualified supplier/second-source coverage + replacement-parts commitment

### Compliance Posture

#### Requirement

Integrates Thor and abides by our security posture and technical min spec.

#### Methodology

* Conduct security audit of firmware, boot chain, and access controls.

#### Measurement

* No unauthorized access vectors — backdoor-free architecture confirmed.

#### Evidence

Scoped security audit report + findings and remediation status + firmware, boot-chain, and access-control review

### Support Structure

#### Requirement

Can provide consistent, ongoing support for the above across hardware, software, and logistics.

#### Methodology

* Review support organization, staffing, and technical competency.  
* Audit ticket-handling infrastructure and escalation procedures.

#### Measurement

* Defined support channels (portal, forum, email minimum).  
* Response-time SLAs by severity tier.  
* Clear escalation path.

#### Evidence

Support-channel links + response-time SLAs by severity + escalation procedures

### Documentation

#### Requirement

Developer-ready documentation enabling independent integration and troubleshooting.

#### Methodology

* Review documentation completeness against GR00T integration workflow.  
* Validate accuracy and version currency of hardware and software guides.

#### Measurement

* Published quick-start guide, hardware integration manual, API reference, and troubleshooting runbook.  
* Publicly accessible documentation portal with search and sample code.

#### Evidence

Documentation portal and sample-code links + completeness and accuracy review against the GR00T integration workflow

# EVALUATION FLOW

The process: who executes, in what order, and how to proceed or halt. 

## Phase 0: Candidate Review

### Objective

Determine if the candidate has baseline intent and capability to enter the evaluation process.

### Methodology

* **Intent screening:** Confirm the candidate's stated goal \- Official GR00T Platform Partner certification vs. Self-Serve adoption.  
* **Capability pre-check:** High-level review against the non-technical gates to identify disqualifying gaps before resource commitment.  
* **Strategic alignment:** Validate that the candidate's target use cases and roadmap align with GR00T scope.

### Proceed / Halt

* Proceed to Phase 1 if intent is confirmed and no disqualifying gaps are identified.  
* Halt if the candidate is outside GR00T scope or lacks minimum commercial viability.

## Phase 1: Support Tier Selection

### Objective

Lock the engagement tier (Official or Self-Serve) and define the evaluation scope.

### Methodology

* **Tier declaration:** Partner selects Official or Self-Serve. Official requires commitment to full admission criteria; Self-Serve requires commitment to technical self-assessment and compliance posture only.  
* **Resource alignment:** NVIDIA assigns GR00T-Ready evaluation interface owner.

### Proceed / Halt

* Proceed to Phase 2 upon signed tier agreement and resource allocation.  
* Halt if the partner cannot commit to the minimum evaluation requirements for the selected tier. Offer Self-Serve path if Official is declined.

## Phase 2: Evaluation

### Objective

Execute the standardized evaluation against GR00T-Ready baselines.

### Measurement

* Each gate scored against the defined criteria in the TECHNICAL and NON-TECHNICAL EVALUATION section.  
* Official: Pass / Conditional / Fail per gate.  
* Self-Serve: Self-reported Compatible / Partial / Not Compatible.

**Item score → gate verdict.** A gate's verdict is derived from the scores of its
applicable items:

* **Fail** — any applicable item scored 0.  
* **Pass** — every applicable item reached the maximum level defined for it.  
* **Conditional** — neither of the above (all items above 0, at least one below its maximum).  
* **Incomplete** — one or more applicable items are untested.

Items the platform cannot support because the measured hardware or feature is
absent (for example F/T sensors on a platform that has none) are marked
**invalid**: they are removed from the gate's totals entirely, contributing to
neither the achieved nor the possible points, and the verdict ignores them. The
absence must be evidenced, not assumed. Self-Serve relabels the same verdicts
Compatible / Partial / Not Compatible.

### Proceed / Halt

* Official: Proceed to Phase 3 if all gates Pass or Conditional (with remediation plan). Halt if any gate receives Fail with no viable remediation path.  
* Self-Serve: No halt mechanism; partner may adopt compatible components regardless of score. No certification is awarded.

## Phase 3: Decision

### Objective

Conclude the evaluation with certification, conditional admission, or rejection.

### Methodology

Path A: Official — All Gates Pass

* Decision: Grant Official GR00T Platform Partner designation.

Path B: Official — Conditional (Remediation Required)

* Iteration: Issue conditional admission with a defined remediation window (e.g., 14 days). Partner addresses gaps (e.g., expands documentation, adds support headcount, fixes security posture).  
* Re-evaluation: NVIDIA re-tests only the conditional gates.  
* Decision: Upgrade to Pass and certify, or downgrade to Fail if remediation is incomplete.

Path C: Official — Conversion to Self-Serve

* Decision: Convert to Self-Serve. No formal certification.  
* Actions: Partners may adopt GR00T components via Self-Serve without restriction. May re-apply for Official evaluation after X months if material improvements are demonstrated.

Path D: Self-Serve — Complete

* Decision: No formal certification. Partner receives confirmation of self-test completion.  
* Actions: Partner may integrate GR00T components as desired.
