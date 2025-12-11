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
                run_command="python main.py",
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
                run_command="python main.py",
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
                run_command="python main.py",
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
                run_command="python main.py",
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
                files=[("main.py", "import os; print(os.environ.get('TEST_VAR', 'not found'))")],
                run_command="python main.py",
                env={"TEST_VAR": "test_value"},
            )
            
            assert "test_value" in result["stdout"]
        finally:
            await runner.cleanup_containers("run-test-5")
            await runner.shutdown()


class TestContainerReuse:
    """Tests for container reuse behavior."""
    
    @pytest.mark.asyncio
    async def test_reuses_container(self):
        """Runner reuses containers for same identifier."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            result1 = await runner.run(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('first')")],
                run_command="python main.py",
            )
            
            result2 = await runner.run(
                identifier="reuse-test",
                language="python",
                files=[("main.py", "print('second')")],
                run_command="python main.py",
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
                run_command="python main.py",
            )
            
            # Second run should not see that file
            result = await runner.run(
                identifier="clean-test",
                language="python",
                files=[("main.py", "import os; print(os.path.exists('test.txt'))")],
                run_command="python main.py",
            )
            
            assert "False" in result["stdout"]
        finally:
            await runner.cleanup_containers("clean-test")
            await runner.shutdown()


class TestDependencyInstallation:
    """Tests for new_dependencies functionality."""
    
    @pytest.mark.asyncio
    async def test_installs_python_dependencies(self):
        """Runner installs Python dependencies and returns packages."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # Setup container first (using container_manager directly)
            container, cached = await runner.container_manager.get_or_create(
                identifier="deps-python-test",
                language="python",
            )
            container_id = container.name
            
            # Run with new dependencies
            result = await runner.run_in_container(
                container_id=container_id,
                files=[("main.py", "import requests; print(requests.__version__)")],
                run_command="python main.py",
                new_dependencies=["requests==2.31.0"],
            )
            
            # Should succeed
            assert result["success"] is True
            assert "2.31.0" in result["stdout"]
            
            # Should return packages
            assert "packages" in result
            assert "requests" in result["packages"]
            assert result["packages"]["requests"] == "2.31.0"
        finally:
            await runner.cleanup_containers("deps-python-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_installs_ruby_dependencies(self):
        """Runner installs Ruby dependencies and returns packages."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # Setup container first
            container, cached = await runner.container_manager.get_or_create(
                identifier="deps-ruby-test",
                language="ruby",
            )
            container_id = container.name
            
            # Run with new dependencies (using rake which is a pure Ruby gem)
            result = await runner.run_in_container(
                container_id=container_id,
                files=[("main.rb", "require 'rake'; puts Rake::VERSION")],
                run_command="ruby main.rb",
                new_dependencies=["rake"],
            )
            
            # Should succeed
            assert result["success"] is True
            assert result["stdout"].strip() != ""  # Should output version
            
            # Should return packages
            assert "packages" in result
            assert "rake" in result["packages"]
        finally:
            await runner.cleanup_containers("deps-ruby-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_installs_shell_dependencies(self):
        """Runner installs Shell dependencies (apk packages)."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # Setup container first
            container, cached = await runner.container_manager.get_or_create(
                identifier="deps-shell-test",
                language="shell",
            )
            container_id = container.name
            
            # Run with new dependencies
            result = await runner.run_in_container(
                container_id=container_id,
                files=[("main.sh", "#!/bin/sh\ncurl --version | head -n1")],
                run_command="sh main.sh",
                new_dependencies=["curl"],
            )
            
            # Should succeed
            assert result["success"] is True
            assert "curl" in result["stdout"].lower()
            
            # Should return packages (apk packages)
            assert "packages" in result
        finally:
            await runner.cleanup_containers("deps-shell-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_no_packages_without_dependencies(self):
        """Runner does not return packages when no dependencies installed."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # Setup container first
            container, cached = await runner.container_manager.get_or_create(
                identifier="no-deps-test",
                language="python",
            )
            container_id = container.name
            
            # Run without new dependencies
            result = await runner.run_in_container(
                container_id=container_id,
                files=[("main.py", "print('hello')")],
                run_command="python main.py",
            )
            
            # Should succeed
            assert result["success"] is True
            
            # Should NOT return packages
            assert "packages" not in result
        finally:
            await runner.cleanup_containers("no-deps-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_handles_dependency_installation_failure(self):
        """Runner handles dependency installation failures gracefully."""
        from runbox.core.runner import CodeRunner, RunError
        
        runner = CodeRunner()
        
        try:
            # Setup container first
            container, cached = await runner.container_manager.get_or_create(
                identifier="deps-fail-test",
                language="python",
            )
            container_id = container.name
            
            # Try to install non-existent package
            with pytest.raises(RunError) as exc_info:
                await runner.run_in_container(
                    container_id=container_id,
                    files=[("main.py", "print('hello')")],
                    run_command="python main.py",
                    new_dependencies=["this-package-does-not-exist-12345"],
                )
            
            assert "Failed to install dependencies" in str(exc_info.value)
        finally:
            await runner.cleanup_containers("deps-fail-test")
            await runner.shutdown()
    
    @pytest.mark.asyncio
    async def test_dependencies_persist_across_runs(self):
        """Installed dependencies persist across multiple runs in same container."""
        from runbox.core.runner import CodeRunner
        
        runner = CodeRunner()
        
        try:
            # Setup container first
            container, cached = await runner.container_manager.get_or_create(
                identifier="deps-persist-test",
                language="python",
            )
            container_id = container.name
            
            # First run: install dependency
            result1 = await runner.run_in_container(
                container_id=container_id,
                files=[("main.py", "import requests; print('installed')")],
                run_command="python main.py",
                new_dependencies=["requests==2.31.0"],
            )
            
            assert result1["success"] is True
            assert "packages" in result1
            
            # Second run: dependency should still be available
            result2 = await runner.run_in_container(
                container_id=container_id,
                files=[("main.py", "import requests; print(requests.__version__)")],
                run_command="python main.py",
                # No new_dependencies this time
            )
            
            assert result2["success"] is True
            assert "2.31.0" in result2["stdout"]
            # Should not return packages since we didn't install anything new
            assert "packages" not in result2
        finally:
            await runner.cleanup_containers("deps-persist-test")
            await runner.shutdown()
