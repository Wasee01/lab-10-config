#!/usr/bin/env python3
"""Real process checks. Build once before invoking. No rebuilds in this file."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / 'target/config-profiles-1.0.0.jar'
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)


def digest():
    return hashlib.sha256(JAR.read_bytes()).hexdigest()


def request(port, path):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=6) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def run(name, profile, expected, external=None, env_value=None, system=None, cli=None):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith(('ENROLLMENT_', 'SPRING_', 'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))}
    if env_value:
        env['ENROLLMENT_RULES_MAXWAITLISTSIZE'] = str(env_value)
    command = ['java']
    if system:
        command += [f'-Denrollment.rules.max-waitlist-size={system}']
    command += ['-jar', str(JAR), f'--server.port={port}', f'--spring.profiles.active={profile}']
    if external:
        command += [f'--spring.config.additional-location=file:{external}/']
    if cli:
        command += [f'--enrollment.rules.max-waitlist-size={cli}']
    with (OUT / f'{name}.log').open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(180):
                if process.poll() is not None:
                    raise AssertionError(f'{name}: startup failed; see log')
                try:
                    status, rules = request(port, '/api/rules')
                    break
                except (OSError, ValueError):
                    time.sleep(0.5)
            else:
                raise AssertionError(f'{name}: startup timed out')
            assert status == 200 and rules['maxWaitlistSize'] == expected, (name, rules)
            if name.startswith('profile'):
                for path in ('env', 'beans', 'configprops', 'loggers', 'shutdown'):
                    assert request(port, '/actuator/' + path)[0] == 404, path
                info_status, info = request(port, '/actuator/info')
                assert info_status == 200 and info['app']['environment'] == profile, info
                assert request(port, '/actuator/metrics')[0] == 200
                health_status, health = request(port, '/actuator/health')
                assert health_status in (200, 503)
                assert {'db', 'rabbit'} <= health['components'].keys(), health
                if os.environ.get('REQUIRE_HEALTH_UP') == 'true':
                    assert health_status == 200, health
                    assert health['components']['db']['status'] == 'UP', health
                    assert health['components']['rabbit']['status'] == 'UP', health
                (OUT / f'{name}-health.json').write_text(json.dumps(health, indent=2))
            return {'case': name, 'expected': expected, 'actual': rules['maxWaitlistSize'], 'sha256': digest()}
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


prediction_commit = subprocess.check_output(
    ['git', 'log', '--reverse', '--format=%H', '--', 'docs/precedence-predictions.md'],
    cwd=ROOT, text=True).splitlines()[0]
original_tree = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', prediction_commit],
                                        cwd=ROOT, text=True)
assert 'src/test/' not in original_tree and 'scripts/verify.py' not in original_tree
subprocess.run(['git', 'merge-base', '--is-ancestor', prediction_commit, 'HEAD'], cwd=ROOT, check=True)
before = digest()
results = []
with tempfile.TemporaryDirectory() as folder:
    Path(folder, 'application.properties').write_text('enrollment.rules.max-waitlist-size=30\n')
    for i in range(1, 7):
        results.append(run(f'precedence-{i}', 'baseline' if i == 1 else 'local', i * 10,
                           folder if i >= 3 else None, 40 if i >= 4 else None,
                           50 if i >= 5 else None, 60 if i >= 6 else None))
for profile, value in [('local', 20), ('prod', 100)]:
    results.append(run('profile-' + profile, profile, value))
assert before == digest(), 'Jar changed between profile runs'
# Real failed startup, rather than only binding a mocked environment.
negative = subprocess.run(['java', '-jar', str(JAR), '--enrollment.rules.max-waitlist-size=-1'],
                          cwd=ROOT, capture_output=True, text=True, timeout=90)
output = negative.stdout + negative.stderr
assert negative.returncode != 0
assert 'enrollment.rules.max-waitlist-size' in output, output
(OUT / 'negative-startup.log').write_text(output)
(OUT / 'verification.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
print('PASS: negative startup, six precedence cases, identical jar, actuator boundary')
