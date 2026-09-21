import pandas as pd

from config import ARCH, DATA_DIR, MALWARE_DIR, BENIGN_DIR


data_file = pd.read_csv(DATA_DIR / f"{ARCH}_medium_tlsh.csv")
mw_filenames = set(data_file[data_file["label"] == 1]["filename"].values.tolist())
bn_filenames = set(data_file[data_file["label"] == 0]["filename"].values.tolist())

mw_dir_filenames = set(f.name for f in MALWARE_DIR.iterdir())
print(f"len(mw_filenames): {len(mw_filenames)}")
print(f"len(mw_dir_filenames): {len(mw_dir_filenames)}")
bn_dir_filenames = set(f.name for f in BENIGN_DIR.iterdir())
print(f"len(bn_filenames): {len(bn_filenames)}")
print(f"len(bn_dir_filenames): {len(bn_dir_filenames)}")


print(f"Number of common malware files: {len(mw_filenames & mw_dir_filenames)}")
print(f"Number of common benign files: {len(bn_filenames & bn_dir_filenames)}")
