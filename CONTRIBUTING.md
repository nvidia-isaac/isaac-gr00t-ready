# Contributing to GR00T-Ready Evaluation

Thank you for your interest in GR00T-Ready Evaluation. Contributions from the
community are welcome, including bug fixes, documentation improvements, new
tests, dashboard improvements, and proposals for evaluation criteria.

## Before you start

- Search the existing [GitHub issues](https://github.com/nvidia-isaac/isaac-gr00t-ready/issues)
  before opening a new one
- Open an issue before starting a large change so the approach can be discussed
- Never include credentials, private robot data, or confidential documentation
  in an issue or pull request

Changes to evaluation criteria can affect scores and compatibility across
evaluations. When proposing a criteria change, explain the reason, provide a
source or test evidence, and describe how existing results may be affected. Do
not reuse an existing criterion ID for a different meaning.

## Set up a development environment

Fork the repository, clone your fork, and create a branch for your change:

```bash
git clone https://github.com/YOUR_USERNAME/isaac-gr00t-ready.git
cd isaac-gr00t-ready
git checkout -b your-change
```

The core toolkit requires Python 3.10 or newer and PyYAML:

```bash
python3 -m pip install pyyaml
```

Robot-specific tests may require additional vendor SDKs or hardware. These are
not required for documentation, scoring, reporting, or dashboard changes.

## Make your change

- Keep each pull request focused on one problem or improvement
- Follow PEP 8 and use type annotations for new Python code
- Add or update tests when behavior changes
- Update user documentation when commands, results, or workflows change
- Preserve stable criterion IDs and explain changes to scoring behavior
- Do not commit generated caches, credentials, or private evaluation evidence

The evaluation pipeline version is maintained in `VERSION`. If a change affects
evaluation outputs or compatibility, call it out in the pull request; the
maintainers will determine whether the version should change.

## Test your change

Run the checks that apply to your contribution. For changes to the core toolkit,
run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q gr00t_ready tests
python3 -m gr00t_ready --version
python3 -m gr00t_ready items
git diff --check
```

If your change requires robot hardware that maintainers may not have, document
the setup, hardware, commands, and observed result in the pull request.

## Submit a pull request

Your pull request should include:

- A clear description of the problem and solution
- A link to any related issue
- The commands or procedures used for testing
- Compatibility or evaluation-version considerations
- Screenshots for visible dashboard changes

All commits must include a Developer Certificate of Origin sign-off. This
project uses the DCO and does not require a Contributor License Agreement (CLA).

## Developer Certificate of Origin

We require that all contributors "sign-off" on their commits. This certifies
that the contribution is your original work, or you have rights to submit it
under the same license, or a compatible license.

Any contribution which contains commits that are not Signed-Off will not be
accepted.

To sign off on a commit, use the `--signoff` (or `-s`) option when committing
your changes:

```bash
git commit -s -m "Describe your change"
```

This adds a line like the following to the commit message:

```text
Signed-off-by: Your Name <your.email@example.com>
```

Use your real name and an email address associated with the commit. The sign-off
certifies the statements in the Developer Certificate of Origin 1.1 below.

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

The canonical DCO text is available at
<https://developercertificate.org/>.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE).
