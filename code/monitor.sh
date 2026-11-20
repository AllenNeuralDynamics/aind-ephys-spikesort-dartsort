#!/usr/bin/env bash
# Debug sampler for the Code Ocean slowdown investigation: every MONITOR_INTERVAL seconds, log
# container memory (cgroup v2 or v1), memory/io pressure, run_capsule.py thread states + read bytes, and GPU state.
INTERVAL=${MONITOR_INTERVAL:-60}
CG=/sys/fs/cgroup
V2_STAT="anon|file|file_mapped|file_dirty|file_writeback|active_file|inactive_file|shmem|pgmajfault|workingset_refault_file"
V1_STAT="total_rss|total_cache|total_mapped_file|total_dirty|total_writeback|total_active_file|total_inactive_file|total_shmem|total_pgmajfault"

log() { echo "[monitor] $(date -u +%FT%TZ) $*"; }

if [ -f $CG/memory.max ]; then
  log "cgroup v2 memory.max=$(cat $CG/memory.max) cpu.max=$(cat $CG/cpu.max 2>/dev/null)"
else
  log "cgroup v1 limit=$(cat $CG/memory/memory.limit_in_bytes 2>/dev/null) cpu_shares=$(cat $CG/cpu/cpu.shares 2>/dev/null)"
fi
log "nproc=$(nproc) host_mem_kb=$(awk '/MemTotal/{print $2}' /proc/meminfo)"
# task filesystem size/usage, and what backs it (model tells EBS from local NVMe instance store)
log "disk $(df -B1 --output=source,fstype,size,used,avail,target "$PWD" /tmp 2>/dev/null | tail -n +2 | tr -s ' ' | tr '\n' ';')"
for d in /sys/block/nvme*; do [ -e "$d" ] && log "blockdev $(basename $d) model=$(cat $d/device/model 2>/dev/null | xargs) size_bytes=$(( $(cat $d/size) * 512 ))"; done

while true; do
  if [ -f $CG/memory.max ]; then
    cur=$(cat $CG/memory.current)
    stat=$(grep -wE "$V2_STAT" $CG/memory.stat | awk '{printf "%s=%s ", $1, $2}')
    mpsi=$(head -1 $CG/memory.pressure 2>/dev/null); ipsi=$(head -1 $CG/io.pressure 2>/dev/null)
  else
    cur=$(cat $CG/memory/memory.usage_in_bytes 2>/dev/null)
    stat=$(grep -wE "$V1_STAT" $CG/memory/memory.stat 2>/dev/null | awk '{printf "%s=%s ", $1, $2}')
    mpsi=$(head -1 /proc/pressure/memory 2>/dev/null); ipsi=$(head -1 /proc/pressure/io 2>/dev/null)
  fi
  log "mem current=$cur $stat"
  log "psi mem[$mpsi] io[$ipsi] load[$(cut -d' ' -f1-3 /proc/loadavg)]"
  pid=$(pgrep -of run_capsule.py)
  if [ -n "$pid" ]; then
    # thread states: R running, S sleeping, D uninterruptible (blocked on I/O or reclaim)
    states=$(cat /proc/$pid/task/*/stat 2>/dev/null | awk '{print $3}' | sort | uniq -c | awk '{printf "%s=%s ", $2, $1}')
    io=$(awk '/^(read_bytes|write_bytes)/{printf "%s ", $0}' /proc/$pid/io 2>/dev/null)
    log "proc pid=$pid threads[$states] $io rss_kb=$(awk '/VmRSS/{print $2}' /proc/$pid/status)"
  fi
  log "gpu $(nvidia-smi --query-gpu=utilization.gpu,memory.used,clocks.sm,clocks.mem,power.draw,temperature.gpu,clocks_throttle_reasons.active --format=csv,noheader 2>&1 | head -1)"
  sleep "$INTERVAL"
done
