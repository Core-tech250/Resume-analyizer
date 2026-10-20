import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.resume_shortlister.evaluation.evaluator import run_benchmark_evaluation

def main():
    print("=" * 80)
    print("  EXPLAINABLE ANONYMIZED RESUME SHORTLISTER - EMPIRICAL BENCHMARK EVALUATION")
    print("=" * 80)
    print("\nRunning benchmark across 60 labeled resumes and 3 job profiles...\n")

    summary = run_benchmark_evaluation()

    print(f"{'Job Title':<45} | {'Candidates':<10} | {'Top-10 Agree':<12} | {'Precision@10':<12} | {'Spearman Rho':<12}")
    print("-" * 100)
    for j in summary.job_results:
        print(f"{j['job_title']:<45} | {j['candidates_count']:<10} | {j['system_top10_agreement']*100:.1f}%{'':<6} | {j['system_precision_at_10']*100:.1f}%{'':<6} | {j['system_spearman_rho']:<12.3f}")

    print("-" * 100)
    print(f"{'OVERALL AGGREGATE':<45} | {summary.total_resumes_evaluated:<10} | {summary.overall_top10_agreement_pct:.1f}%{'':<6} | {summary.overall_precision_at_10_pct:.1f}%{'':<6} | {summary.overall_spearman_rho:<12.3f}")
    print("=" * 100)

    print("\n[+] BASELINE COMPARISON:")
    print(f"  * Our Anonymized Multi-Factor Ranker Top-10 Agreement : {summary.overall_top10_agreement_pct:.1f}%")
    print(f"  * Naive Keyword-Counting Screener Top-10 Agreement    : {summary.keyword_baseline_agreement_pct:.1f}%")
    print(f"  * Measured Accuracy Lift over Keyword Baseline        : +{summary.accuracy_lift_pct:.1f}%\n")

    print("[*] VERIFIED RESUME BULLET POINT (Section 9):")
    print(f'"{summary.resume_bullet_text}"\n')

if __name__ == "__main__":
    main()
