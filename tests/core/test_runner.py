"""Tests for code runner - focusing on run behavior."""

import pytest


class TestCodeRun:
    """Tests for code run behavior."""
    
    @pytest.mark.asyncio
    async def test_runs_simple_python(self):
        """Runner runs simple Python code."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result = await runner.run(
                identifier="run-test-1",
                language="python",
                files=[("main.py", "print('hello')")],
                entrypoint="main.py",
            )
            
            assert result["success"] is True
            assert result["exit_code"] == 0
            assert "hello" in result["stdout"]
        finally:
            await runner.cleanup_containers("run-test-1")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_captures_stderr(self):
        """Runner captures standard error."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result = await runner.run(
                identifier="run-test-2",
                language="python",
                files=[("main.py", "import sys; sys.stderr.write('error output')")],
                entrypoint="main.py",
            )
            
            assert "error output" in result["stderr"]
        finally:
            await runner.cleanup_containers("run-test-2")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_returns_exit_code(self):
        """Runner returns correct exit code."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result = await runner.run(
                identifier="run-test-3",
                language="python",
                files=[("main.py", "import sys; sys.exit(42)")],
                entrypoint="main.py",
            )
            
            assert result["success"] is False
            assert result["exit_code"] == 42
        finally:
            await runner.cleanup_containers("run-test-3")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_handles_multiple_files(self):
        """Runner handles multiple files."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result = await runner.run(
                identifier="run-test-4",
                language="python",
                files=[
                    ("helper.py", "def greet(name): return f'Hello, {name}!'"),
                    ("main.py", "from helper import greet; print(greet('World'))"),
                ],
                entrypoint="main.py",
            )
            
            assert result["success"] is True
            assert "Hello, World!" in result["stdout"]
        finally:
            await runner.cleanup_containers("run-test-4")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_environment_variables(self):
        """Runner passes environment variables."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result = await runner.run(
                identifier="run-test-5",
                language="python",
                files=[("main.py", "import os; print(os.environ['MY_VAR'])")],
                entrypoint="main.py",
                env={"MY_VAR": "test_value"},
            )
            
            assert result["success"] is True
            assert "test_value" in result["stdout"]
        finally:
            await runner.cleanup_containers("run-test-5")
            await runner.shutdown()


class TestContainerReuse:
    """Tests for container reuse behavior."""
    
    @pytest.mark.asyncio
    async def test_reuses_container(self):
        """Runner reuses container for same identifier."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # First run
            result1 = await runner.run(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('first')")],
                entrypoint="main.py",
            )
            
            # Second run
            result2 = await runner.run(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('second')")],
                entrypoint="main.py",
            )
            
            assert result1["container_id"] == result2["container_id"]
            assert result1["cached"] is False
            assert result2["cached"] is True
        finally:
            await runner.cleanup_containers("reuse-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleans_files_between_runs(self):
        """Runner cleans files between runs."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # First run creates a file
            await runner.run(
                identifier="clean-test",
                language="python",
                files=[("main.py", "open('test.txt', 'w').write('data')")],
                entrypoint="main.py",
            )
            
            # Second run should not see that file
            result = await runner.run(
                identifier="clean-test",
                language="python",
                files=[("main.py", "import os; print(os.path.exists('test.txt'))")],
                entrypoint="main.py",
            )
            
            assert "False" in result["stdout"]
        finally:
            await runner.cleanup_containers("clean-test")
            await runner.shutdown()

