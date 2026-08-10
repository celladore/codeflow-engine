"""
Tests for platform detection and Windows adaptations.
"""

from unittest.mock import patch

from codeflow_engine.actions.quality_engine.platform_detector import PlatformDetector


class TestPlatformDetector:
    """Test platform detection functionality."""

    def test_platform_detection_windows(self):
        """Test platform detection on Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()

            assert detector.platform == "windows"
            assert detector.is_windows is True
            assert detector.is_linux is False
            assert detector.is_macos is False

    def test_platform_detection_linux(self):
        """Test platform detection on Linux."""
        with patch("platform.system", return_value="Linux"):
            detector = PlatformDetector()

            assert detector.platform == "linux"
            assert detector.is_windows is False
            assert detector.is_linux is True
            assert detector.is_macos is False

    def test_platform_detection_macos(self):
        """Test platform detection on macOS."""
        with patch("platform.system", return_value="Darwin"):
            detector = PlatformDetector()

            assert detector.platform == "darwin"
            assert detector.is_windows is False
            assert detector.is_linux is False
            assert detector.is_macos is True

    def test_platform_detection_unknown(self):
        """Test platform detection for unknown platform."""
        with patch("platform.system", return_value="Unknown"):
            detector = PlatformDetector()

            assert detector.platform == "unknown"
            assert detector.is_windows is False
            assert detector.is_linux is False
            assert detector.is_macos is False

    def test_windows_limitations(self):
        """Test Windows limitations detection."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            limitations = detector.get_windows_limitations()

            assert isinstance(limitations, list)
            assert len(limitations) > 0
            assert any("CodeQL" in limitation for limitation in limitations)
            assert any("Docker" in limitation for limitation in limitations)

    def test_windows_alternatives(self):
        """Test Windows alternatives for tools."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            alternatives = detector.get_windows_alternatives()

            assert isinstance(alternatives, dict)
            assert "codeql" in alternatives
            assert "docker_tools" in alternatives

            # Check that alternatives are provided
            codeql_alternatives = alternatives["codeql"]
            assert len(codeql_alternatives) > 0
            assert any("semgrep" in alt.lower() for alt in codeql_alternatives)
            assert any("bandit" in alt.lower() for alt in codeql_alternatives)

    def test_windows_recommendations(self):
        """Test Windows recommendations."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            recommendations = detector.get_windows_recommendations()

            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            assert any("Semgrep" in rec for rec in recommendations)
            assert any("WSL2" in rec for rec in recommendations)

    def test_cross_platform_tools(self):
        """Test cross-platform tools list."""
        detector = PlatformDetector()
        tools = detector.get_cross_platform_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "semgrep" in tools
        assert "ruff" in tools
        assert "bandit" in tools
        assert "mypy" in tools

    def test_tool_filtering_windows(self):
        """Test tool filtering on Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()

            all_tools = [
                "ruff",
                "mypy",
                "bandit",
                "codeql",
                "semgrep",
                "windows_security",
            ]
            available_tools = detector.get_available_tools(all_tools)

            # Windows-compatible tools should be included
            assert "ruff" in available_tools
            assert "mypy" in available_tools
            assert "bandit" in available_tools
            assert "semgrep" in available_tools

            # CodeQL should be excluded on Windows
            assert "codeql" not in available_tools

            # Windows security tool should be included but with warning
            assert "windows_security" in available_tools

    def test_tool_filtering_linux(self):
        """Test tool filtering on Linux."""
        with patch("platform.system", return_value="Linux"):
            detector = PlatformDetector()

            all_tools = [
                "ruff",
                "mypy",
                "bandit",
                "codeql",
                "semgrep",
                "windows_security",
            ]
            available_tools = detector.get_available_tools(all_tools)

            # All tools should be available on Linux
            assert "ruff" in available_tools
            assert "mypy" in available_tools
            assert "bandit" in available_tools
            assert "codeql" in available_tools
            assert "semgrep" in available_tools
            assert "windows_security" in available_tools

    def test_tool_substitutions_windows(self):
        """Test tool substitutions on Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            substitutions = detector.get_tool_substitutions()

            assert isinstance(substitutions, dict)
            assert "codeql" in substitutions
            assert substitutions["codeql"] == "semgrep"

    def test_tool_substitutions_linux(self):
        """Test tool substitutions on Linux."""
        with patch("platform.system", return_value="Linux"):
            detector = PlatformDetector()
            substitutions = detector.get_tool_substitutions()

            # No substitutions needed on Linux
            assert isinstance(substitutions, dict)
            assert len(substitutions) == 0

    def test_platform_info_structure(self):
        """Test platform info structure."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            info = detector.detect_platform()

            assert isinstance(info, dict)
            assert "platform" in info
            assert "is_windows" in info
            assert "is_linux" in info
            assert "is_macos" in info
            assert "python_version" in info
            assert "architecture" in info

            assert info["platform"] == "windows"
            assert info["is_windows"] is True
            assert info["is_linux"] is False
            assert info["is_macos"] is False

    def test_detector_instances(self):
        """Test that detector creates separate instances."""
        detector1 = PlatformDetector()
        detector2 = PlatformDetector()

        # Should be separate instances (not singleton)
        assert detector1 is not detector2
        # But should have same platform detection
        assert detector1.platform == detector2.platform

    def test_windows_warning_message(self):
        """Test Windows warning message generation."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()

            # Test that warning message is generated
            # This would typically be used in logging or user interface
            limitations = detector.get_windows_limitations()
            assert len(limitations) > 0

            recommendations = detector.get_windows_recommendations()
            assert len(recommendations) > 0

    def test_platform_detection_edge_cases(self):
        """Test platform detection edge cases."""
        # Test with empty string
        with patch("platform.system", return_value=""):
            detector = PlatformDetector()
            assert detector.platform == ""

        # Test with lowercase
        with patch("platform.system", return_value="windows"):
            detector = PlatformDetector()
            assert detector.platform == "windows"

    def test_tool_categories(self):
        """Test tool categorization."""
        # Test that tools are properly categorized
        all_tools = ["ruff", "mypy", "bandit", "codeql", "semgrep", "windows_security"]

        # These should be in the windows_compatible set
        windows_compatible = {"ruff", "mypy", "bandit", "semgrep"}

        # These should be in the windows_incompatible set
        windows_incompatible = {"codeql"}

        # These should be in the windows_careful set

        # Verify categorization logic. PlatformDetector caches is_windows in __init__,
        # so it must be constructed inside the patch — building it outside made this
        # test assert against the real host and pass only on Windows.
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            available_tools = detector.get_available_tools(all_tools)

            for tool in windows_compatible:
                assert tool in available_tools

            for tool in windows_incompatible:
                assert tool not in available_tools

            assert (
                "windows_security" in available_tools
            )  # Should be included with warning
