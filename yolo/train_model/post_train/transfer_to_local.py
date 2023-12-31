from sshtools.transfer import scp

src_root = "/home/ubuntu/GitRepos/ml_arcs/yolo/train_model"
dst_root = "/home/nicholas/GitRepos/ml_arcs/yolo/train_model"

files_to_move = [
    "/state_dicts/yolo_train3.pth",
    "/state_dicts/yolo_val3.pth",
    "/lossdfs/train3.csv",
    "/lossdfs/val3.csv",
]

user = "nicholas"
ip = "174.72.155.21"
port = "2201"

for file in files_to_move:
    scp(src_root + file, dst_root + file, user, ip, port)
