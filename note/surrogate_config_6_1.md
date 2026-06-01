# Surrogate LightGBM Config

Ghi chu nay tong hop cau hinh dang dung de train/check surrogate LightGBM cho `sorelFFNN`.

## Khai niem

- Target that: `sorelFFNN`, dung model `malware_rl/envs/utils/sorelFFNN.pt`.
- Surrogate: LightGBM, train trong `surrogate.py` bang `lightgbm.train(...)`.
- File surrogate sau khi train:

```text
malware_rl/envs/utils/lgb_sorelFFNN_model_<seed>.txt
```

Vi du voi seed `39720`:

```text
malware_rl/envs/utils/lgb_sorelFFNN_model_39720.txt
```

## Dataset PE hien tai

Train malware folder dang dung:

```text
$HOME/RL/dataset/main_dataset/RL/virus
```

Benign train folder:

```text
$HOME/RL/dataset/main_dataset/RL/benign
```

Virus folder co dang family:

```text
virus/
  Locker/
  Mediyes/
  Winwebsec/
  Zbot/
  Zeroaccess/
```

Script export se quet de quy cac family nay. Family chi duoc ghi vao manifest de trace, khong phai label train. Label train la binary:

```text
benign = 0
virus/malware = 1
```

## Export dataset cho surrogate

Surrogate khong train truc tiep tu PE raw. No can feature vector EMBER/SOREL 2381 chieu dang memmap:

```text
X_val.dat
y_val.dat
X_test.dat
y_test.dat
```

Trong code hien tai, ten `val` thuc te duoc dung lam train set cho surrogate:

```text
X_val.dat/y_val.dat   = train data cho LightGBM surrogate
X_test.dat/y_test.dat = test/eval data de tinh threshold/FPR
```

Lenh export mau:

```bash
python scripts/export_ember_dat.py \
  --out ember_dat \
  --val-benign "$HOME/RL/dataset/main_dataset/RL/benign" \
  --val-malware "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-benign "$HOME/RL/dataset/test_dataset/RL/benign" \
  --test-malware "$HOME/RL/dataset/test_dataset/RL/virus" \
  --skip-errors
```

Neu can chay nen:

```bash
nohup python scripts/export_ember_dat.py \
  --out ember_dat \
  --val-benign "$HOME/RL/dataset/main_dataset/RL/benign" \
  --val-malware "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-benign "$HOME/RL/dataset/test_dataset/RL/benign" \
  --test-malware "$HOME/RL/dataset/test_dataset/RL/virus" \
  --skip-errors \
  > export_ember_dat.log 2>&1 &
```

Theo doi:

```bash
tail -f export_ember_dat.log
```

Khi xong can thay:

```bash
ls -lh ember_dat
```

Du file:

```text
X_val.dat
y_val.dat
X_test.dat
y_test.dat
val_manifest.csv
test_manifest.csv
```

## Path surrogate.py dang doc

`surrogate.py` dang hard-code SOREL data o:

```text
/data/mari/sorel-data
```

Neu export ra `ember_dat`, tao symlink:

```bash
sudo mkdir -p /data/mari
sudo ln -s "$HOME/RL/meme_modify/ember_dat" /data/mari/sorel-data
```

Kiem tra:

```bash
ls -lh /data/mari/sorel-data/X_val.dat \
       /data/mari/sorel-data/y_val.dat \
       /data/mari/sorel-data/X_test.dat \
       /data/mari/sorel-data/y_test.dat
```

## Kiem tra rieng surrogate LightGBM

Can co memory do RL target tao ra:

```text
data/memory/sorelFFNN/observations.npy
data/memory/sorelFFNN/scores.npy
```

Kiem tra:

```bash
ls -lh data/memory/sorelFFNN/observations.npy \
       data/memory/sorelFFNN/scores.npy
```

Xem shape:

```bash
python - <<'PY'
import numpy as np
x = np.load("data/memory/sorelFFNN/observations.npy", mmap_mode="r")
y = np.load("data/memory/sorelFFNN/scores.npy", mmap_mode="r")
print("observations:", x.shape)
print("scores:", y.shape)
PY
```

Chay train surrogate rieng, khong can doi full pipeline:

```bash
python - <<'PY'
from surrogate import train_surrogate

threshold = train_surrogate(
    target="sorelFFNN",
    data_path="data/memory/sorelFFNN",
    save_model_path="malware_rl/envs/utils",
    seed=39720,
)

print("SURROGATE OK")
print("threshold:", threshold)
PY
```

Kiem tra model da tao:

```bash
ls -lh malware_rl/envs/utils/lgb_sorelFFNN_model_39720.txt
```

Neu file tren ton tai thi surrogate LightGBM da train duoc.

## Chay full MEME pipeline co surrogate

Luu y:

- `--train-dir` va `--test-dir` cua RL evasion nen tro vao malware samples, vi env se modify malware de evade.
- Dataset `.dat` cua surrogate van can ca benign va malware nhu phan export ben tren.
- `--eval_timesteps` la phase dau query target `sorelFFNN`.
- Sau phase dau, code moi train LightGBM surrogate va chuyen sang `lgb-train-v0`.

Lenh mau:

```bash
nohup python ppo_model_extract.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test/virus" \
  --eval_timesteps 59648 \
  --num_timesteps 59648 \
  --num_rounds 1 \
  > ppo_model_extract.out 2>&1 & echo $! > ppo_model_extract.pid
```

Theo doi:

```bash
tail -f ppo_model_extract.out
```

Kiem tra process:

```bash
cat ppo_model_extract.pid
ps -p $(cat ppo_model_extract.pid) -o pid,etime,cmd
```

Kiem tra da toi surrogate chua:

```bash
ls -lh malware_rl/envs/utils/lgb_sorelFFNN_model_*.txt
```

Neu chua co file `lgb_sorelFFNN_model_*.txt`, pipeline van dang o phase target `sorelFFNN` hoac chua train surrogate xong.

## Smoke test nhanh

Neu chi muon test pipeline co chay toi surrogate duoc khong, dung timesteps nho:

```bash
nohup python ppo_model_extract.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test/virus" \
  --eval_timesteps 256 \
  --num_timesteps 256 \
  --num_rounds 1 \
  > ppo_model_extract_smoke.out 2>&1 & echo $! > ppo_model_extract_smoke.pid
```

Theo doi:

```bash
tail -f ppo_model_extract_smoke.out
```

## Cac loi da gap

### No module named malware_rl

Nguyen nhan: chay script trong `scripts/` lam Python khong thay repo root.

Da sua `scripts/export_ember_dat.py` de tu load extractor theo path repo.

### Automatic train/test splitting is disabled

Nguyen nhan: import package `malware_rl` lam chay `malware_rl/__init__.py`, file nay bat buoc co train/test env vars.

Ban moi cua `scripts/export_ember_dat.py` load truc tiep `malware_rl/envs/utils/ember.py`, khong import ca package `malware_rl`.

Neu gap lai, kiem tra file script co doan:

```python
import importlib.util
EMBER_MODULE_PATH = REPO_ROOT / "malware_rl" / "envs" / "utils" / "ember.py"
```

va khong con dong:

```python
from malware_rl.envs.utils.ember import PEFeatureExtractor
```

### Input path does not exist

Vi du:

```text
FileNotFoundError: Input path does not exist: /home/rl/RL/dataset/test_dataset/RL/benign
```

Nguyen nhan: path test/benign hoac test/virus khong dung.

Tim path dung:

```bash
find "$HOME/RL/dataset" -maxdepth 5 -type d \( -iname "benign" -o -iname "virus" \)
```

