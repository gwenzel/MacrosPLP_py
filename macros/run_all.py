from pathlib import Path
from interface.commands import plp_commands, plexos_commands
from interface.macros_runner import execute_commands
from utils.logger import create_logger, add_file_handler
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path)


logger = create_logger('run_all')
add_file_handler(logger, 'run_all', Path(__file__).parent)


# Functions to interact with remote server
@timeit
def generate_inputs(file_path: Path, commands: list):
    # Check if file_path is valid file
    if (not Path(file_path.get()).exists()) or (
            not Path(file_path.get()).is_file()):
        logger.info("Please select a valid file.")
        return
    # Select inputs if any
    selected_inputs = [commands[i]['description']
                       for i, _ in enumerate(commands)]
    logger.info(f"Generating Inputs: {', '.join(selected_inputs)}")
    # Actual logic to generate the selected inputs for A
    bool_dict = {
        commands[i]['description']: True
        for i, _ in enumerate(commands)
        }
    parallel_dict = {
        commands[i]['description']: commands[i]['parallel']
        for i, _ in enumerate(commands)
    }
    command_dict = {
        commands[i]['description']: (
            commands[i]['command'] + ' -f "' + file_path.get() + '"')
        for i, _ in enumerate(commands)
        }
    if any(bool_dict.values()):
        logger.info("Inputs running.")
        execute_commands(bool_dict, parallel_dict, command_dict, logger)
    else:
        logger.warning(("No inputs selected."))
    logger.info("Inputs generated. Please validate files.")


@timeit
def main():
    '''
    Main routine
    '''
    try:
        # Get input file path
        logger.info('Getting input file path')
        parser = define_arg_parser()
        iplp_path = get_iplp_input_path(parser)

        # Generate plp inputs
        generate_inputs(iplp_path, plp_commands)

        # Wait until plp inputs are done and run plexos
        generate_inputs(iplp_path, plexos_commands)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
