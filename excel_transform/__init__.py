import json
import logging
import os
import pathlib
import sys
from collections import OrderedDict
from datetime import datetime

import click
import humanfriendly
import pandas

__version__ = '1.1.0'


logger = logging.getLogger()


@click.group()
@click.option('--debug', is_flag=True)
@click.pass_context
def cli(ctx, debug):
    """
    This is a tool to generate an excel file based on a provided source excel and transformation mapping
    """
    log_format = '%(asctime)s|%(levelname)s|%(name)s|(%(funcName)s):-%(message)s'
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, stream=sys.stdout, format=log_format)
    logger.info(f'{"-" * 20} Starting Logging for {ctx.invoked_subcommand} (v{__version__}) {"-" * 20}')


def process_column_mappings(source_df, column_mappings):
    out_df = source_df.copy(deep=True)
    name_map = {}
    exclude_columns = []
    pending_columns = False
    for x in column_mappings:
        if x[0][:3] == '[-]':
            exclude_columns.append(x[0][3:])
        elif x[0] == '*':
            pending_columns = True
        else:
            name_map.update({x[0]: x[1] if x[1] != '_' else x[0]})
    index_map = {'_': []}
    for mapping in column_mappings:
        index = mapping[2]
        value = mapping[0] if mapping[1] == '_' else mapping[1]
        if index == '_':
            if value != '*' and value[:3] != '[-]':
                index_map['_'].append(value)
            continue
        if index not in index_map:
            index_map[index] = value
            exclude_columns.append(value)
        else:
            raise Exception(f'Cannot have same column index for multiple columns, please check your column mapping\n'
                            f'{index=}, {mapping=}')
    out_df = out_df.rename(columns=name_map)
    pending_columns_list = list(set(out_df.columns).difference(exclude_columns)) if pending_columns else []
    return {'df': out_df, 'index_map': index_map, 'pending_columns': pending_columns_list}


def process_mappings(source_df_dict, mappings):
    worksheets_dict = {}
    for mapping in mappings:
        count = -1
        for sheet_identifier, sheet_mapping in mapping.items():
            count += 1
            entry = get_dict_entry(count, sheet_identifier, source_df_dict)
            sheet_name = entry.get('name')
            if sheet_name not in worksheets_dict:
                # noinspection PyArgumentList
                worksheets_dict.update({sheet_name: {
                    'source': entry.get('item').copy(deep=True),
                    'dest': {}
                }})
            dest_sheet_name = sheet_mapping.get('dest_worksheet_name') or sheet_name
            dest_sheet_name = sheet_name if dest_sheet_name == '_' else dest_sheet_name
            mapping_processed = process_column_mappings(worksheets_dict.get(sheet_name).get('source'),
                                                        sheet_mapping.get('columns'))
            mapping_processed.update({'merge_columns': sheet_mapping.get('merge_columns')})
            worksheets_dict[sheet_name]['dest'].update({dest_sheet_name: mapping_processed})
    return worksheets_dict


@cli.command()
@click.argument('source', nargs=-1)
@click.argument('mapping')
@click.option('-o', '--output', help='relative or absolute path to output file')
@click.option('--individual', help='performs processing on an individual file basis', is_flag=True)
@click.pass_context
def transform(ctx, **kwargs):
    transform_spreadsheets(**kwargs)


def transform_spreadsheets(source, mapping, output):
    """Produces a new spreadsheet with transformation mapping applied"""
    s_time = datetime.now()
    try:
        source_paths = [get_path(x) for x in source]
        mapping_path = get_path(mapping, make_dir=False)
        output_path = get_path(output or 'excel_transform_output.xlsx', make_dir=True)
        source_dfs = OrderedDict()
        try:
            logger.info('processing mappings file')
            with open(mapping_path) as f:
                mappings = json.load(f)
        except Exception as e:
            logger.critical(f'Encountered error trying to read the mapping file:\n{e}')
            sys.exit()
        logger.info('processing source files')
        for source_path in source_paths:
            try:
                source_dfs.update({source_path.stem: pandas.read_excel(source_path, sheet_name=None)})
            except Exception as e:
                logger.critical(f'Encountered error processing source file: {source_path}\n{e}')
                sys.exit()

        count = -1
        processed_source = {}
        for identifier, mapping in mappings.items():
            count += 1
            if '__' == identifier[:2]:
                continue
            entry = get_dict_entry(count, identifier, source_dfs)
            logger.info(f'processing mappings for: {entry.get("name")}')
            processed_source.update({entry.get('name'): process_mappings(entry.get("item"), mapping)})

        logger.info('grouping processed source data by destination worksheet')
        dest_worksheet_dict = {}
        for worksheets in processed_source.values():
            for data in worksheets.values():
                for dest_worksheet_name, dest_data in data['dest'].items():
                    if dest_worksheet_name not in dest_worksheet_dict:
                        dest_worksheet_dict[dest_worksheet_name] = []
                    dest_worksheet_dict[dest_worksheet_name].append(dest_data)

        logger.info('merging destination worksheet data')
        out_dict = {}
        for dest_worksheet_name, data_list in dest_worksheet_dict.items():
            temp_df = pandas.DataFrame()
            columns = {'_': [], '*': [], 'indexed': {}}
            for data in data_list:
                columns['_'].extend(data['index_map']['_'])
                columns['*'].extend(data['pending_columns'])
                for index, column_name in data['index_map'].items():
                    if index == '_':
                        continue
                    if index not in columns['indexed']:
                        columns['indexed'][index] = column_name
                    else:
                        raise Exception(f'Cannot have same column index for multiple columns, please check your'
                                        f' column mapping\n{dest_worksheet_name=}, {column_name=}, {index=}')
                if temp_df.empty:
                    temp_df = data.get('df')
                else:
                    temp_df = pandas.merge(temp_df, data.get('df'), how='outer', on=data.get('merge_columns'))
            sorted_column_list = []
            i = 0
            while len(columns['_']) > 0 or len(columns['*']) > 0:
                if str(i) in columns['indexed']:
                    column_name = columns['indexed'][str(i)]
                elif len(columns['_']) > 0:
                    column_name = columns['_'].pop()
                else:
                    column_name = columns['*'].pop()
                if column_name not in sorted_column_list:
                    sorted_column_list.append(column_name)
                i += 1
            out_dict[dest_worksheet_name] = temp_df[sorted_column_list]

        logger.info(f'generating merged excel spreadsheet')
        writer = pandas.ExcelWriter(output_path, engine='openpyxl')
        for sheet_name, df in out_dict.items():
            try:
                logger.info(f'processing sheet: {sheet_name}')
                df.to_excel(writer, sheet_name=sheet_name, index=False, )
            except Exception as e:
                logger.error(f'encountered error processing sheet: {sheet_name}\n{e}')
        try:
            writer.save()
        except Exception as e:
            logger.critical(f'encountered error trying to save spreadsheet: {output_path}\n{e}')

    except Exception as e:
        logger.critical(f'Encountered unexpected error:\n{e}')
    processing_time = humanfriendly.format_timespan(datetime.now() - s_time)
    logger.info(f'done processing in {processing_time}')


def get_dict_entry(iteration_index, identifier, iterable):
    if isinstance(identifier, int) or identifier.isdigit() or identifier == '_':
        index = iteration_index if identifier == '_' else int(identifier) - 1
        df = list(iterable.values())[index]
        name = list(iterable)[index]
    else:
        df = iterable[identifier]
        name = identifier
    return {'name': name, 'item': df}


@cli.command()
@click.option('-o', '--output', help='relative or absolute path to output file')
def mapping_skeleton(**kwargs):
    """Generates a skeleton of the mapping file"""
    try:
        out_path = get_path(output or 'mapping_skeleton.json', make_dir=True)

        skeleton = {
            '__instructions__': {
                '1': 'names starting with double underscore (\'__\') will be ignored',
                '2': 'fields enclosed with \'<>\' should be replaced completely',
                '3': 'use the underscore character (\'_\') to use system defaults',
                '4': 'use the asterisk character (\'*\') as a wildcard in the columns list to ensure all other'
                     ' columns are included. Note that when asterisk is used, column name and position will be default'
                     ' and all other column mappings will be ignored therefore the asterisk should only be used at the'
                     ' end of the mapping',
                '5': 'in the column mappings, use the following notation to exclude a column from the output: [-]',
                '6': 'note that the merge_columns need to match on the respective sheets that are being merged'
            },
            '<spreadsheet 1 name> or <position> or _': [
                {
                    '<worksheet 1 name> or _': {
                        'dest_worksheet_name': '<dest worksheet name> or _',
                        'merge_columns': '[<name of reference columns for merging multiple spreadsheets>]',
                        'columns': [
                            ['<column 1 name>', '<column 1 dest name> or _', '<column 1 dest position> or _'],
                            ['<column 2 name>', '<column 2 dest name> or _', '<column 2 dest position> or _']
                        ]
                    }
                },
                {
                    '<worksheet 2 name> or _': {
                        'dest_worksheet_name': '<dest worksheet name> or _',
                        'merge_columns': '[<name of reference columns for merging multiple spreadsheets>]',
                        'columns': [
                            ['<column 1 name>', '<column 1 dest name> or _', '<column 1 dest position> or _'],
                            ['<column 2 name>', '<column 2 dest name> or _', '<column 2 dest position> or _']
                        ]
                    }
                }
            ],
            '<spreadsheet 2 name> or <position> or _': [
                {
                    '<worksheet 1 name> or _': {
                        'dest_worksheet_name': '<dest worksheet name> or _',
                        'merge_columns': '[<name of reference columns for merging multiple spreadsheets>]',
                        'columns': [
                            ['<column 1 name>', '<column 1 dest name> or _', '<column 1 dest position> or _']
                        ]
                    }
                }
            ]
        }
        with open(out_path, 'w+') as f:
            json.dump(skeleton, f, indent=2)

    except Exception as e:
        logger.critical(f'Encountered unexpected error:\n{e}')


def get_path(path, make_dir=True):
    out_path = pathlib.Path(path)
    if not out_path.is_absolute():
        out_path = pathlib.Path(os.getcwd()) / out_path
    if make_dir and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True)
    return out_path


@cli.command()
def gui():
    """Launches a PYQT5 gui"""
    from excel_transform.gui import launch_gui
    launch_gui()


@cli.command()
def version():
    """Shows the version of the application"""
    click.echo(f'v{__version__}')


if __name__ == '__main__':
    cli()
