# Changes Made

## SOREL-FFNN as default detector

- Changed the default RL target from `ember` to `sorelFFNN` in:
  - `ppo.py`
  - `random_agent.py`
  - `evaluate.py`
  - `ppo_model_extract.py`
- Added target aliases so these values are accepted and normalized to `sorelFFNN`:
  - `sorelFFNN`
  - `SOREL-FFNN`
  - `sorel-ffnn`
  - `sorel_ffnn`
  - `sorelffnn`

## Dataset folder structure

- Changed dataset loading to support recursive family folders under:

```text
malware_rl/envs/utils/samples/
```

- Expected folder structure:

```text
malware_rl/envs/utils/samples/Locker/...
malware_rl/envs/utils/samples/Mediyes/...
malware_rl/envs/utils/samples/Winwebsec/...
malware_rl/envs/utils/samples/Zbot/...
malware_rl/envs/utils/samples/Zeroaccess/...
```

- Added empty `.gitkeep` placeholders for those family folders.
- Updated `malware_rl/envs/utils/interface.py` so sample ids keep the relative family path, for example:

```text
Locker/<filename>
Zbot/<filename>
```

## Train/test split saving

- Updated `malware_rl/__init__.py` so it no longer automatically creates a 70/30 train/test split.
- The code now requires an explicit dataset source:
  - provide both train and test folders, or
  - provide an existing split manifest with `MALWARE_RL_SPLIT_FILE`.
- If external train/test folders are provided, the code uses those exact folders:
  - `*-train-v0` environments load samples only from the train folder.
  - `*-test-v0` environments load samples only from the test folder.
- External paths can be provided with CLI args:

```bash
python ppo.py --train-dir <train_folder> --test-dir <test_folder>
python evaluate.py --agent <model.zip> --train-dir <train_folder> --test-dir <test_folder>
```

- Or with environment variables:

```bash
MALWARE_RL_TRAIN_DIR=<train_folder>
MALWARE_RL_TEST_DIR=<test_folder>
```

- Split output folder:

```text
data/splits/samples/
```

- Files created when the code runs:

```text
data/splits/samples/split.json
data/splits/samples/train.txt
data/splits/samples/test.txt
data/splits/samples/train/<family>/samples.txt
data/splits/samples/test/<family>/samples.txt
```

- Because automatic splitting is disabled, `MALWARE_RL_SPLIT_SEED` is no longer used to create a new split.

- The split output directory can be changed with:

```text
MALWARE_RL_SPLIT_DIR=<path>
```

- An existing split can be selected with:

```text
MALWARE_RL_SPLIT_FILE=data/splits/samples/split.json
```

- The code saves only manifest files, not copies of the binary samples.
- `split.json` stores each split root plus relative sample paths, so future runs can reload the same dataset with:

```bash
MALWARE_RL_SPLIT_FILE=data/splits/samples/split.json
```

## Evasion output structure

- Updated all gym environments so evasion outputs preserve the original family folder.
- Example:

```text
Input sample:
malware_rl/envs/utils/samples/Locker/abc.exe

Output evasion:
data/evaded/sorelFFNN/Locker/<sha256_of_modified_file>
```

- Updated environments:
  - `malware_rl/envs/malconv_gym.py`
  - `malware_rl/envs/ember_gym.py`
  - `malware_rl/envs/sorel_gym.py`
  - `malware_rl/envs/sorelFFNN_gym.py`
  - `malware_rl/envs/AV_gym.py`
  - `malware_rl/envs/lgb_gym.py`
  - `malware_rl/envs/custom_gym.py`

## Save evasion only during test

- Kept `sorelFFNN-train-v0` with:

```python
"save_modified_data": False
```

- Changed `sorelFFNN-test-v0` to:

```python
"save_modified_data": True
```

- Changed `sorel-test-v0` to:

```python
"save_modified_data": True
```

- Changed `custom-train-v0` to:

```python
"save_modified_data": False
```

so train does not write modified evasion files.

## PPO max turns and train/test run command

- Changed the shared environment max turns default to `10` in `malware_rl/__init__.py`.
- Added environment override support:

```python
MAXTURNS = int(os.getenv("MALWARE_RL_MAXTURNS", "10"))
```

- Added `--maxturns` to `ppo.py`, so this command can control the registered train/test gym environments.

- Command requested for running PPO with explicit train/test dataset folders:

```bash
python ppo.py \
  --target sorelFFNN \
  --train-dir dataset/train \
  --test-dir dataset/test \
  --num-episodes 5961 \
  --num-queries 59610 \
  --maxturns 10
```

- Linux one-line command after activating the virtual environment:

```bash
python ppo.py --target sorelFFNN --train-dir dataset/train --test-dir dataset/test --num-episodes 5961 --num-queries 59610 --maxturns 10
```

## Memory output folders

- Added automatic creation of `data/memory/...` folders in envs that write `observations.npy` and `scores.npy`.
- This fixes errors like:

```text
FileNotFoundError: data/memory/sorelFFNN/observations.npy
```

## Verification

- Ran syntax check with `ast.parse`.
- Result:

```text
syntax ok
```

- Full RL execution was not run because the workspace currently does not include real samples or `sorelFFNN.pt`.

## Linux bash command to run PPO with direct dataset paths

- This is a Linux bash command.
- This command does not activate/change the virtual environment.
- It passes the dataset paths directly into the code through CLI arguments:
  - train data: `~/RL/dataset/main_dataset/RL/virus/`
  - test data: `~/RL/dataset/main_dataset/test/`
- The code then uses:
  - `--train-dir` for the train environment.
  - `--test-dir` for the test environment.

```bash
python ppo.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test" \
  --num-episodes 5961 \
  --num-queries 59610 \
  --maxturns 10
```

- One-line Linux command:

```bash
python ppo.py --target sorelFFNN --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" --test-dir "$HOME/RL/dataset/main_dataset/test" --num-episodes 5961 --num-queries 59610 --maxturns 10
```

- If you want to use another dataset location, only change these two arguments:

```bash
--train-dir "/path/to/your/train"
--test-dir "/path/to/your/test"
```

## Linux troubleshooting: `ppo.py: error: unrecognized arguments --train-dir --test-dir --maxturns`

- This means the Linux machine is still running an older `ppo.py` that does not have the new CLI args yet.
- Because `git pull` was blocked by local changes in `malware_rl/__init__.py`, the new `ppo.py` was not pulled.

- If you do not want to change/stash the local code yet, run with environment variables instead:

```bash
export MALWARE_RL_TRAIN_DIR="$HOME/RL/dataset/main_dataset/RL/virus"
export MALWARE_RL_TEST_DIR="$HOME/RL/dataset/main_dataset/test"
export MALWARE_RL_MAXTURNS=10

python ppo.py \
  --target sorelFFNN \
  --num-episodes 5961 \
  --num-queries 59610
```

- Do not quote `~` like `"~/..."` because quoted `~` may not expand. Prefer `$HOME/...`.

- If you want to pull the newest code first, save or remove the local change, then pull:

```bash
git status
git stash push -m "local changes before pulling train-test args"
git pull
```

- After the pull succeeds, the direct CLI command works:

```bash
source .venv37_clean/bin/activate
python ppo.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test" \
  --num-episodes 5961 \
  --num-queries 59610 \
  --maxturns 10
```
chạy với suggorate
```bash
source .venv37_clean/bin/activate
nohup python ppo_model_extract.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test" \
  --eval_timesteps 59610 \
  --num_timesteps 59610 \
  --num_rounds 1 \
  > ppo_model_extract.out 2>&1 & echo $! > ppo_model_extract.pid
```

rl@rl-VMware-Virtual-Platform:~/RL/meme_modify$ source .venv37_clean/bin/activate
nohup python ppo_model_extract.py \
  --target sorelFFNN \
  --train-dir "$HOME/RL/dataset/main_dataset/RL/virus" \
  --test-dir "$HOME/RL/dataset/main_dataset/test" \
  --eval_timesteps 59610 \
  --num_timesteps 59610 \
  --num_rounds 1 \
  > ppo_model_extract.out 2>&1 & echo $! > ppo_model_extract.pid
[1] 890612