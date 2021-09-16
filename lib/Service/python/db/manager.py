from enum import Enum
from datetime import datetime
import time
import os
import re
from . import occ_cloud
from .connectors import create_connection, internal_handle_db_connect_exception


# @copyright Copyright (c) 2021 Andrey Borysenko <andrey18106x@gmail.com>
#
# @copyright Copyright (c) 2021 Alexander Piskun <bigcat88@icloud.com>
#
# @author 2021 Alexander Piskun <bigcat88@icloud.com>
#
# @license AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class DbType(Enum):
    MYSQL = 1
    PGSQL = 3
    OCI = 4
    UNKNOWN = -1


DatabaseProvider = ''
Config = {}
Errors = []
Warnings = []
Connections = [{}, {}]  # {type: Optional[pymysql | pg8000], impl: Optional[implementation_class]}


def init_cloud_config(map_schema: dict) -> bool:
    global Config, Errors
    result = True
    for our_key in map_schema.keys():
        success, value_of_key = occ_cloud.get_cloud_config_value(map_schema[our_key])
        if not success:
            Errors.append(f"Cant find `{map_schema[our_key]}` value in cloud config.")
            result = False
        else:
            Config[our_key] = value_of_key
    return result


def detect_msql_socket(config: dict, _php_info: str) -> None:
    global Warnings
    socket_path = config['dbhost'].split(":")[-1]
    if os.path.exists(socket_path):
        config['usock'] = socket_path
        return
    if not config['dbport'] and _php_info:
        m_groups = re.search(r'pdo_mysql\.default_socket\s*=>\s*(.*)\s*=>\s*(.*)',
                             _php_info, flags=re.MULTILINE + re.IGNORECASE)
        if m_groups is None:
            Warnings.append("Cant parse php info.")
            return
        socket_path = m_groups.groups()[-1].strip()
        if os.path.exists(socket_path):
            config['usock'] = socket_path


def detect_pgsql_socket(config: dict, _php_info: str) -> None:
    socket_path = config['dbhost'].split(":")[-1]
    if os.path.exists(socket_path):
        config['usock'] = socket_path


def init():
    global Config, DatabaseProvider, Warnings
    occ_cloud.init()
    map_schema = {'datadir': 'datadirectory',
                  'dbname': 'dbname',
                  'dbtprefix': 'dbtableprefix',
                  'dbuser': 'dbuser',
                  'dbpassword': 'dbpassword',
                  'dbhost': 'dbhost',
                  'dbport': 'dbport',
                  'dbtype': 'dbtype'}
    Config['usock'] = ''
    if not init_cloud_config(map_schema):
        return DbType.UNKNOWN
    php_ok, php_info = occ_cloud.php_call('-r', "phpinfo();")
    if not php_ok:
        php_info = ''
        Warnings.append("Cant get php info.")
    if Config['dbtype'] == 'mysql':
        detect_msql_socket(Config, php_info)
        DatabaseProvider = 'pymysql'
        return DbType.MYSQL
    if Config['dbtype'] == 'pgsql':
        detect_pgsql_socket(Config, php_info)
        DatabaseProvider = 'pg8000'
        return DbType.PGSQL
    if Config['dbtype'] == 'oci':
        return DbType.OCI
    return DbType.UNKNOWN


def internal_get_connection_by_id(connection_id: int) -> dict:
    if connection_id not in (0, 1):
        raise ValueError('connection_id can be currently only 0 or 1.')
    return Connections[connection_id]


def internal_get_connection(connection_id: int, error_out: list = None) -> dict:
    connection = internal_get_connection_by_id(connection_id)
    if connection.get('type', None) is not None and connection.get('impl', None) is not None:
        return connection
    impl = create_connection(Config, DatabaseProvider, error_out=error_out)
    if impl is not None:
        connection['impl'] = impl
        connection['type'] = DatabaseProvider
        return connection
    return {}


def internal_execute_fetchall(query: str, connection: dict, args=None) -> list:
    if connection['type'] == 'pg8000':
        if args is None:
            args = ()
    result = []
    cur = connection['impl'].cursor()
    try:
        cur.execute(query, args)
        if cur.rowcount is not None:
            if cur.rowcount > 0:
                result = cur.fetchall()
                keys = [k[0] for k in cur.description]
                result = [dict(zip(keys, row)) for row in result]
    finally:
        cur.close()
    return result


def internal_execute_commit(query: str, connection: dict, args=None) -> int:
    if connection['type'] == 'pg8000':
        if args is None:
            args = ()
    result = 0
    cur = connection['impl'].cursor()
    try:
        cur.execute(query, args)
        if cur.rowcount is not None:
            if cur.rowcount > 0:
                result = cur.rowcount
                connection['impl'].commit()
    finally:
        cur.close()
    return result


def close_connection(connection_id: int = 0):
    connection = internal_get_connection_by_id(connection_id)
    if connection.get('type', None) is not None and connection.get('impl', None) is not None:
        try:
            if connection['type'] == 'pymysql':
                connection['impl'].close()
            elif connection['type'] == 'pg8000':
                connection['impl'].close()
        except Exception as exception_info:
            print(f'Exception({type(exception_info).__name__}) when closing DB:{str(exception_info)}')
    connection['impl'] = None
    connection['type'] = None


def execute_fetchall(query: str, args=None, connection_id: int = 0) -> list:
    result = []
    for _ in range(3):
        connection = internal_get_connection(connection_id)
        if not connection:
            time.sleep(1)
            continue
        try:
            result = internal_execute_fetchall(query=query, connection=connection, args=args)
            break
        except Exception as exception_info:
            internal_handle_db_connect_exception(exception_info)
        close_connection(connection_id)
    return result


def execute_commit(query: str, args=None, connection_id: int = 0) -> int:
    result = 0
    for _ in range(3):
        connection = internal_get_connection(connection_id)
        if not connection:
            time.sleep(1)
            continue
        try:
            result = internal_execute_commit(query=query, connection=connection, args=args)
            break
        except Exception as exception_info:
            internal_handle_db_connect_exception(exception_info)
        close_connection(connection_id)
    return result


def get_required_packages() -> dict:
    if DatabaseProvider == 'pg8000':
        return {'asn1crypto': 'asn1crypto'}
    return {}


def get_optional_packages() -> dict:
    if DatabaseProvider == 'pymysql':
        return {'cryptography': 'cryptography', 'nacl': 'pynacl'}
    return {}


def get_boost_packages() -> dict:
    return {}


def get_warnings() -> list:
    return Warnings


def check_db() -> list:
    if Errors:
        return Errors
    if not DatabaseProvider:
        return [f"Unsupported DB type:`{Config['dbtype']}`"]
    ret = []
    success = False
    try:
        connection = internal_get_connection(0, ret)
        if connection:
            close_connection(0)
            success = True
    except Exception as exception_info:
        ret.append(f'Exception({type(exception_info).__name__}):{str(exception_info)}')
    finally:
        if not success:
            ret.append('Cant connect to database.')
    return ret


def get_task_table_name() -> str:
    return Config['dbtprefix'] + 'mediadc_tasks'


def get_task_details_table_name() -> str:
    return Config['dbtprefix'] + 'mediadc_tasks_details'


def get_image_table_name() -> str:
    return Config['dbtprefix'] + 'mediadc_photos'


def get_video_table_name() -> str:
    return Config['dbtprefix'] + 'mediadc_videos'


def get_settings_table_name() -> str:
    return Config['dbtprefix'] + 'mediadc_settings'


def get_storage_table_name() -> str:
    return Config['dbtprefix'] + 'storages'


def get_mounts_table_name() -> str:
    return Config['dbtprefix'] + 'mounts'


def get_ext_mounts_table_name() -> str:
    return Config['dbtprefix'] + 'external_mounts'


def get_fs_table_name() -> str:
    return Config['dbtprefix'] + 'filecache'


def get_mimetypes_table_name() -> str:
    return Config['dbtprefix'] + 'mimetypes'


def get_time() -> int:
    return int(datetime.now().timestamp())
