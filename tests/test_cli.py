"""
Tests for the command-line interface module of DescribePDF.

This module tests the CLI functionality for converting PDF files to markdown descriptions.
"""

from unittest.mock import patch, MagicMock, call
from argparse import Namespace

from describepdf import cli

class TestCLI:
    """Test suite for the CLI functionality."""

    def test_setup_cli_parser(self):
        """Test the CLI argument parser configuration."""
        # Execute test
        parser = cli.setup_cli_parser()
        
        # Assert results
        assert parser.description is not None
        assert parser.epilog is not None
        
        # Check that required arguments are configured
        actions = {action.dest: action for action in parser._actions}
        assert "pdf_file" in actions
        assert "output" in actions
        assert "api_key" in actions
        assert "local" in actions
        assert "endpoint" in actions
        assert "vlm_model" in actions
        assert "language" in actions
        assert "use_markitdown" in actions
        assert "use_summary" in actions
        assert "summary_model" in actions
        assert "verbose" in actions

    def test_create_progress_callback(self):
        """Test the creation and behavior of the progress callback function."""
        # Setup test
        mock_tqdm = MagicMock()
        
        with patch('describepdf.cli.tqdm', return_value=mock_tqdm):
            # Execute test
            callback = cli.create_progress_callback()
            
            # Call the callback with different progress values
            callback(0.5, "Halfway done")
            callback(0.7, "More progress")
            callback(1.0, "Complete")
            
            # Assert results
            cli.tqdm.assert_called_once_with(total=100, desc="Processing", unit="%")
            
            # Verify tqdm was updated correctly
            assert mock_tqdm.update.call_count == 3
            mock_tqdm.set_description.assert_has_calls([
                call("Halfway done"),
                call("More progress"),
                call("Complete")
            ])
            
            # Verify tqdm was closed at the end
            mock_tqdm.close.assert_called_once()

    def test_run_cli_file_not_found(self):
        """Test handling when the input PDF file does not exist."""
        # Setup test
        args = Namespace(
            pdf_file="nonexistent.pdf",
            output=None,
            api_key=None,
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)

    def test_run_cli_verbose_mode(self):
        """Test setting up logging when verbose mode is enabled."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key=None,
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=True
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={}), \
             patch('describepdf.cli.core.convert_pdf_to_markdown', return_value=("Error", None)), \
             patch('describepdf.cli.logger.setLevel') as mock_set_level, \
             patch('sys.exit'):
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            import logging
            mock_set_level.assert_called_once_with(logging.DEBUG)

    def test_run_cli_missing_openrouter_api_key(self):
        """Test handling when OpenRouter API key is required but missing."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key=None,
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"openrouter_api_key": None}), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)

    def test_run_cli_ollama_not_available(self):
        """Test handling when Ollama is requested but not available."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key=None,
            local=True,  # Use Ollama
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"ollama_endpoint": "http://localhost:11434"}), \
             patch('describepdf.cli.ollama_client.OLLAMA_AVAILABLE', False), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)

    def test_run_cli_ollama_not_running(self):
        """Test handling when Ollama is not running."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key=None,
            local=True,  # Use Ollama
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"ollama_endpoint": "http://localhost:11434"}), \
             patch('describepdf.cli.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.cli.ollama_client.check_ollama_availability', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)

    def test_run_cli_successful_conversion(self):
        """Test successful conversion and saving of result."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output="output.md",
            api_key="test_key",
            local=False,
            endpoint=None,
            vlm_model="test_model",
            language="English",
            use_markitdown=True,
            use_summary=False,
            summary_model=None,
            verbose=False
        )
        
        env_config = {
            "openrouter_api_key": "env_key",
            "or_vlm_model": "env_model",
            "output_language": "Spanish",
            "use_markitdown": False,
            "use_summary": False
        }
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value=env_config), \
             patch('describepdf.cli.create_progress_callback', return_value=MagicMock()), \
             patch('describepdf.cli.core.convert_pdf_to_markdown', 
                   return_value=("Conversion completed successfully.", "# Markdown content")), \
             patch('builtins.open', MagicMock()):
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            # Verify convert_pdf_to_markdown was called with the correct configuration
            _, kwargs = cli.core.convert_pdf_to_markdown.call_args
            assert kwargs["pdf_path"] == "test.pdf"
            assert kwargs["cfg"]["provider"] == "openrouter"
            assert kwargs["cfg"]["openrouter_api_key"] == "test_key"  # From args, not env
            assert kwargs["cfg"]["vlm_model"] == "test_model"  # From args, not env
            assert kwargs["cfg"]["output_language"] == "English"  # From args, not env
            assert kwargs["cfg"]["use_markitdown"] is True  # From args, not env
            
            # Verify file was opened for writing
            open.assert_called_once_with("output.md", "w", encoding="utf-8")

    def test_run_cli_default_output_filename(self):
        """Test generation of default output filename when not specified."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,  # No output specified
            api_key="test_key",
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"openrouter_api_key": "test_key"}), \
             patch('describepdf.cli.create_progress_callback', return_value=MagicMock()), \
             patch('describepdf.cli.core.convert_pdf_to_markdown', 
                   return_value=("Conversion completed successfully.", "# Markdown content")), \
             patch('builtins.open', MagicMock()):
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            # Verify file was opened with default filename
            open.assert_called_once_with("test_description.md", "w", encoding="utf-8")

    def test_run_cli_conversion_failure(self):
        """Test handling when conversion fails."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key="test_key",
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"openrouter_api_key": "test_key"}), \
             patch('describepdf.cli.create_progress_callback', return_value=MagicMock()), \
             patch('describepdf.cli.core.convert_pdf_to_markdown', 
                   return_value=("Error in conversion.", None)), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)

    def test_run_cli_error_saving_output(self):
        """Test handling when saving output file fails."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output="output.md",
            api_key="test_key",
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False
        )
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
             patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.cli.config.get_config', return_value={"openrouter_api_key": "test_key"}), \
             patch('describepdf.cli.create_progress_callback', return_value=MagicMock()), \
             patch('describepdf.cli.core.convert_pdf_to_markdown', 
                   return_value=("Conversion completed successfully.", "# Markdown content")), \
             patch('builtins.open', side_effect=IOError("Permission denied")), \
             patch('sys.exit') as mock_exit:
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            mock_exit.assert_called_once_with(1)
    
    def test_run_cli_with_page_selection(self):
        """Test running CLI with page selection."""
        # Setup test
        args = Namespace(
            pdf_file="test.pdf",
            output=None,
            api_key="test_key",
            local=False,
            endpoint=None,
            vlm_model=None,
            language=None,
            use_markitdown=None,
            use_summary=None,
            summary_model=None,
            verbose=False,
            pages="1,3,5-10"
        )
        
        env_config = {
            "openrouter_api_key": "env_key",
            "or_vlm_model": "env_model",
            "output_language": "Spanish",
            "use_markitdown": False,
            "use_summary": False
        }
        
        with patch('describepdf.cli.setup_cli_parser', return_value=MagicMock()), \
            patch('describepdf.cli.setup_cli_parser().parse_args', return_value=args), \
            patch('os.path.exists', return_value=True), \
            patch('os.path.isfile', return_value=True), \
            patch('describepdf.cli.config.get_config', return_value=env_config), \
            patch('describepdf.cli.create_progress_callback', return_value=MagicMock()), \
            patch('describepdf.cli.core.convert_pdf_to_markdown', 
                return_value=("Conversion completed successfully.", "# Markdown content")), \
            patch('builtins.open', MagicMock()):
            
            # Execute test
            cli.run_cli()
            
            # Assert results
            # Verify convert_pdf_to_markdown was called with the correct configuration
            _, kwargs = cli.core.convert_pdf_to_markdown.call_args
            assert kwargs["cfg"]["provider"] == "openrouter"
            assert kwargs["cfg"]["page_selection"] == "1,3,5-10" 