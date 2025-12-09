"""Tests for code executor - focusing on execution behavior."""

import pytest


class TestCodeExecution:
    """Tests for code execution behavior."""
    
    @pytest.mark.asyncio
    async def test_executes_simple_python(self):
        """Executor runs simple Python code."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            result = await executor.execute(
                identifier="exec-test-1",
                language="python",
                files=[("main.py", "print('hello')")],
                entrypoint="main.py",
            )
            
            assert result["success"] is True
            assert result["exit_code"] == 0
            assert "hello" in result["stdout"]
        finally:
            await executor.cleanup_containers("exec-test-1")
            await executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_captures_stderr(self):
        """Executor captures standard error."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            result = await executor.execute(
                identifier="exec-test-2",
                language="python",
                files=[("main.py", "import sys; sys.stderr.write('error output')")],
                entrypoint="main.py",
            )
            
            assert "error output" in result["stderr"]
        finally:
            await executor.cleanup_containers("exec-test-2")
            await executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_returns_exit_code(self):
        """Executor returns correct exit code."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            result = await executor.execute(
                identifier="exec-test-3",
                language="python",
                files=[("main.py", "import sys; sys.exit(42)")],
                entrypoint="main.py",
            )
            
            assert result["success"] is False
            assert result["exit_code"] == 42
        finally:
            await executor.cleanup_containers("exec-test-3")
            await executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_handles_multiple_files(self):
        """Executor handles multiple files."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            result = await executor.execute(
                identifier="exec-test-4",
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
            await executor.cleanup_containers("exec-test-4")
            await executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_environment_variables(self):
        """Executor passes environment variables."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            result = await executor.execute(
                identifier="exec-test-5",
                language="python",
                files=[("main.py", "import os; print(os.environ['MY_VAR'])")],
                entrypoint="main.py",
                env={"MY_VAR": "test_value"},
            )
            
            assert result["success"] is True
            assert "test_value" in result["stdout"]
        finally:
            await executor.cleanup_containers("exec-test-5")
            await executor.shutdown()


class TestContainerReuse:
    """Tests for container reuse behavior."""
    
    @pytest.mark.asyncio
    async def test_reuses_container(self):
        """Executor reuses container for same identifier."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            # First execution
            result1 = await executor.execute(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('first')")],
                entrypoint="main.py",
            )
            
            # Second execution
            result2 = await executor.execute(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('second')")],
                entrypoint="main.py",
            )
            
            assert result1["container_id"] == result2["container_id"]
            assert result1["cached"] is False
            assert result2["cached"] is True
        finally:
            await executor.cleanup_containers("reuse-test")
            await executor.shutdown()
    
    @pytest.mark.asyncio
    async def test_cleans_files_between_executions(self):
        """Executor cleans files between executions."""
        from runbox.core.executor import CodeExecutor
        
        executor = CodeExecutor()
        
        try:
            # First execution creates a file
            await executor.execute(
                identifier="clean-test",
                language="python",
                files=[("main.py", "open('test.txt', 'w').write('data')")],
                entrypoint="main.py",
            )
            
            # Second execution should not see that file
            result = await executor.execute(
                identifier="clean-test",
                language="python",
                files=[("main.py", "import os; print(os.path.exists('test.txt'))")],
                entrypoint="main.py",
            )
            
            assert "False" in result["stdout"]
        finally:
            await executor.cleanup_containers("clean-test")
            await executor.shutdown()

