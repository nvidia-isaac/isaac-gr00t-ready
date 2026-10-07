# Robot test cases

Prepare and run test cases using `criteria/criteria.yaml` and the robot's
documentation and SDK. Score measured results against the item's rubric; leave
unrun tests untested. Conventions:

- One test script per criteria item, named after the item id:
  `test_HW_OC_01.py`, `test_SW_IMU_06.py`, ...
- Each script prints a single JSON line as its last output:
  `{"id": "HW-OC-01", "score": 2, "evidence": "JetPack 7.0 (r38.1), latest", "notes": ""}`
- `automation: auto` items must run unattended (typically over SSH to the robot).
- `automation: semi` items may prompt the operator for physical setup, then measure.
- `automation: manual` items are checklists — `manual_checklist.md` in this
  directory collects them with step-by-step instructions and a place to record
  the score and evidence.
- Tests are prepared and executed one criteria item at a time, and the result is
  recorded into `../results/results.yaml` immediately after each run — so the
  evaluation can stop and resume at any point with progress intact.
- `run_all.py` (optional, written by the evaluator) re-executes every existing
  auto/semi test and merges the JSON outputs into `../results/results.yaml` —
  useful for regression re-runs after a firmware/SDK update, not for the initial
  one-by-one pass.

## Safe execution

Follow the vendor's setup and safety procedures. Before any motion test, the
operator must confirm that the robot is supported as required, the area is
clear, and an E-stop is within reach. Motion scripts must require operator
confirmation before each movement, load vendor joint limits, reject targets
outside those limits, and use conservative amplitudes and speeds with
interpolated trajectories. Announce each movement and verify the resulting
position through both operator observation and state read-back.

For long tests, verify the data stream and setup in a short initial run, show
live progress, and stop if the stream or test conditions become invalid. Save
logs under `output/` and make runs interruptible. Record measured values and
supporting evidence in `../results/results.yaml` immediately after each test,
preserving the checklist's `evaluation_version`.
