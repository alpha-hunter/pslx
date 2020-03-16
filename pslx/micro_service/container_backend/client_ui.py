import argparse
from flask import Flask, render_template, request
from pslx.micro_service.container_backend.client import ContainerBackendClient
from pslx.micro_service.container_backend.rpc import ContainerBackendRPC
from pslx.schema.enums_pb2 import Status, ModeType, DataModelType
from pslx.schema.storage_pb2 import ContainerBackendValue
from pslx.storage.partitioner_storage import MinutelyPartitionerStorage
from pslx.storage.proto_table_storage import ProtoTableStorage
from pslx.util.env_util import EnvUtil
from pslx.util.file_util import FileUtil
from pslx.util.proto_util import ProtoUtil

container_backend_rpc_client_ui = Flask(
    __name__,
    template_folder='templates',
    static_folder='../../ui'
)
container_backend_rpc_client_ui.config.update(
    SECRET_KEY='PSLX_CONTAINER_BACKEND_UI'
)
parser = argparse.ArgumentParser()
parser.add_argument('--server_url', dest='server_url', default="", type=str, help='The server url.')
parser.add_argument('--root_certificate_path', dest='root_certificate_path', default="",
                    type=str, help='Path to the root certificate.')
args = parser.parse_args()
root_certificate = None
if args.root_certificate_path:
    with open(FileUtil.die_if_file_not_exist(file_name=args.root_certificate_path), 'r') as infile:
        root_certificate = infile.read()

container_backend_client = ContainerBackendClient(
    client_name=ContainerBackendClient.get_class_name() + '_FLASK_BACKEND',
    server_url=args.url,
    root_certificate=root_certificate
)


def read_container_info():
    backend_folder = FileUtil.join_paths_to_dir(
        root_dir=EnvUtil.get_pslx_env_variable('PSLX_DATABASE'),
        base_name=ContainerBackendRPC.get_class_name()
    )
    containers_info = {}
    for sub_dirs in FileUtil.list_dirs_in_dir(dir_name=backend_folder):
        for sub_dir in sub_dirs:
            sub_sub_dirs = FileUtil.list_dirs_in_dir(dir_name=sub_dir)
            dir_to_containers = ''
            for sub_sub_dir in sub_sub_dirs:
                if 'ttl' in sub_sub_dir:
                    dir_to_containers = sub_sub_dir
                else:
                    dir_to_containers = sub_dir
                break
            if dir_to_containers:
                for dir_name in FileUtil.list_dirs_in_dir(dir_name=dir_to_containers):
                    container_name = dir_name.split('/')[-1].strip('/')
                    storage = MinutelyPartitionerStorage()
                    storage.initialize_from_dir(dir_name=dir_name)
                    latest_dir = storage.get_latest_dir()
                    files = FileUtil.list_files_in_dir(dir_name=latest_dir)
                    if not files:
                        continue
                    proto_table_storage = ProtoTableStorage()
                    proto_table_storage.initialize_from_file(file_name=files[0])
                    result_proto = proto_table_storage.read(
                        params={
                            'key': container_name,
                            'message_type': ContainerBackendValue,
                        }
                    )
                    containers_info[result_proto.contain_name] = {
                        'status': result_proto.container_status,
                        'updated_time': result_proto.updated_time,
                        'mode': ProtoUtil.get_name_by_value(enum_type=ModeType, value=result_proto.mode),
                        'data_model': ProtoUtil.get_name_by_value(
                            enum_type=DataModelType, value=result_proto.data_model),
                    }
                    operators_info = []
                    for key, val in dict(result_proto.operator_status_map).items():
                        operators_info.append({
                            'operator_name': key,
                            'status': ProtoUtil.get_name_by_value(
                                enum_type=DataModelType, value=val),
                            'updated_time': result_proto.updated_time,
                        })
                    containers_info[result_proto.contain_name]['operators_info'] = operators_info

    return containers_info


@container_backend_rpc_client_ui.route("/", methods=['GET', 'POST'])
@container_backend_rpc_client_ui.route("/index.html", methods=['GET', 'POST'])
def index():
    containers_info = read_container_info()
    return render_template(
        'index.html',
        containers_info=containers_info
    )


@container_backend_rpc_client_ui.route('/view_container', methods=['GET', 'POST'])
def view_container():
    # TODO
    pass
