import re
import signal

from cgcrepair.core.handlers.database import TestOutcome
from cgcrepair.utils.data import Test

pid_pattern = "# pid (\d{4,7})"
polls_failed_pattern = "# polls failed: (\d{1,4})"
pid_debug_pattern = "# \[DEBUG\] pid: (\d{1,7}), sig: (\d{1,2})"
pid_process_pattern = "# Process generated signal \(pid: (\d{1,7}), signal: (\d{1,2})\)"
not_ok_pattern = "not ok - (.*)"
ok_pattern = "ok - (.*)"

pov_signals = [signal.SIGSEGV, signal.SIGILL, signal.SIGBUS]


def get_outcome(output: str, test: Test, sig: int):
    """
        Parses out the number of passed and failed tests from cb-test output
    """
    test_outcome = TestOutcome()
    test_outcome.total = 1
    test_outcome.passed = 0
    test_outcome.name = test.name
    test_outcome.is_pov = test.is_pov
    test_outcome.polls_failed = polls_failed(output)
    test_outcome.sig = sig

    if 'timed out' in output:
        test_outcome.error = "Test timed out"
        test_outcome.result = True

    elif not test.is_pov and test_outcome.polls_failed > 0:
        test_outcome.error = f"{test_outcome.polls_failed} polls failed"
        test_outcome.result = True

    # If the test failed to run, consider it failed
    elif 'TOTAL TESTS' not in output:
        test_outcome.error = f"Test failed to run."
        test_outcome.result = False

    elif 'TOTAL TESTS: ' in output:
        test_outcome.total = int(output.split('TOTAL TESTS: ')[1].split('\n')[0])
        test_outcome.passed = int(output.split('TOTAL PASSED: ')[1].split('\n')[0])
        ok = match_pattern(output, ok_pattern)
        not_ok = match_pattern(output, not_ok_pattern)

        if not_ok:
            test_outcome.status = not_ok
            test_outcome.result = False
        elif ok:
            test_outcome.status = ok
            test_outcome.result = True
    else:
        test_outcome.error = "Unknown behavior"
        test_outcome.result = False

    return test_outcome


def get_pids_sig(output: str):
    match = re.search(pid_debug_pattern, output)
    match2 = re.search(pid_process_pattern, output)
    pids = []
    sig = 0

    if match:
        pids.append(match.group(1))
        sig = int(match.group(2))
    elif match2:
        pids.append(match2.group(1))
        sig = int(match2.group(2))
    else:
        match = re.search(pid_pattern, output)
        if match:
            pids.append(match.group(1))

    return pids, sig


def polls_failed(output: str):
    match = re.search(polls_failed_pattern, output)

    if match:
        return int(match.group(1))

    return 0


def match_pattern(output: str, pattern: str):
    match = re.search(pattern, output)

    if match:
        return match.group(1)

    return None
