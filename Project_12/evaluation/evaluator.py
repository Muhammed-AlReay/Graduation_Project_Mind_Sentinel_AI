from ragas import evaluate
from datasets import Dataset

from ragas.metrics import (
    faithfulness,
    context_precision,
    context_recall,
    answer_relevancy,
    answer_correctness,
)

from llm_router import get_llm
from langchain_huggingface import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL

import pandas as pd
import time
import os


def run_rag_evaluation(rag_chain, dataset):

    results = []

    print("\n🔄 Running RAG Evaluation...\n")

    total_questions = len(dataset)

    for idx, item in enumerate(dataset, start=1):

        print(f"[{idx}/{total_questions}] Processing...")

        max_retries = 5

        success = False

        for attempt in range(max_retries):

            try:

                response = rag_chain.invoke({
                    "input": item["question"],
                    "chat_history": []
                })

                answer = response.get("answer", "").strip()

                contexts = [
                    doc.page_content
                    for doc in response.get("context", [])
                ]

                if not answer:
                    print("⚠️ Empty answer skipped")
                    break

                results.append({
                    "question": item["question"],
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": item["ground_truth"]
                })

                success = True

                time.sleep(3)

                break

            except Exception as e:

                error_msg = str(e)

                if "429" in error_msg:

                    wait_time = 60 * (attempt + 1)

                    print(
                        f"⚠️ Rate Limit "
                        f"Retry {attempt+1}/{max_retries}"
                    )

                    print(
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:

                    print(
                        f"❌ Error on question:"
                    )

                    print(item["question"])

                    print(error_msg)

                    break

        if not success:
            print("⏭️ Skipped")

    if len(results) == 0:
        raise ValueError(
            "No successful evaluation results!"
        )

    print(
        f"\n✅ Collected {len(results)} successful answers"
    )

    os.makedirs("evaluation_results", exist_ok=True)

    pd.DataFrame(results).to_csv(
        "evaluation_results/raw_results.csv",
        index=False
    )

    print(
        "💾 Raw results saved."
    )

    ds = Dataset.from_list(results)

    print("\n🔄 Running RAGAS Metrics...\n")

    try:

        score = evaluate(
            ds,
            metrics=[
                faithfulness,
                context_precision,
                context_recall,
                answer_relevancy,
                answer_correctness,
            ],
            llm=get_llm(),
            embeddings=HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL
            ),
        )

        score_df = score.to_pandas()

        score_df.to_csv(
            "evaluation_results/ragas_detailed_scores.csv",
            index=False
        )

        score_dict = (
            score_df
            .mean(numeric_only=True)
            .to_dict()
        )

        print("\n========== RAGAS RESULTS ==========\n")

        for metric, value in score_dict.items():

            print(
                f"{metric:<25}: {value:.4f}"
            )

        print("\n===================================\n")

        return score_dict, results

    except Exception as e:

        print(
            "\n❌ RAGAS Metrics Failed"
        )

        print(str(e))

        print(
            "\n💡 Most likely reason:"
        )

        print(
            "OpenRouter daily quota exhausted."
        )

        return {}, results