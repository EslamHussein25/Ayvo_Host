import pandas as pd
from openai import OpenAI
import time
import json

# Setup client
client = OpenAI(api_key="")

def evaluate_model_answer(category, question, golden_answer, model_answer, context, model_name):
    """
    Evaluate model answer based on three criteria
    """
        
    evaluation_prompt = f"""
    You are an expert in evaluating AI systems. Please evaluate the {model_name} answer based on the following criteria:

    *Context:*
    {context}

    *Question:*
    {question}

    *Golden Answer (Reference):*
    {golden_answer}

    *{model_name} Answer:*
    {model_answer}

    *Question Category:*
    {category}

    Please evaluate the {model_name} answer on the following criteria from 1 to 10:

    1. *Faithfulness (vs Context-Free)*: How well the answer adheres to the given context without fabricating information outside of it
    - 10: Answer is completely based on the given context
    - 5: Answer is partially based on context with some external information
    - 1: Answer ignores context or fabricates information

    2. *Answer Relevance (vs Incomplete)*: How relevant and complete the answer is to the question
    - 10: Answer is completely relevant and complete
    - 5: Answer is relevant but incomplete or contains unnecessary information
    - 1: Answer is irrelevant or very incomplete

    3. *Context Relevance (vs Noisy Context)*: How well the most relevant parts of the context are used
    - 10: Used the most relevant parts of the context
    - 5: Used some relevant parts while ignoring important sections
    - 1: Did not use the relevant parts of the context

    4. *correctness (vs Golden Answer)*: How accurate the answer is compared to the golden/reference answer
    - 10: Answer is completely correct and aligns perfectly with the golden answer
    - 5: Answer is partially correct with some key information matching the golden answer
    - 1: Answer is incorrect or contradicts the golden answer

    Return the result in JSON format only:
    {{
        "faithfulness": <score from 1-10>,
        "answer_relevance": <score from 1-10>,
        "context_relevance": <score from 1-10>,
        "correctness": <score from 1-10>,
        "overall_score": <average of all four scores>,
        "explanation": "Brief explanation of the evaluation"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in evaluating AI systems. Please respond in JSON format only."},
                {"role": "user", "content": evaluation_prompt}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Evaluation error for {model_name}: {e}")
        return {
            "faithfulness": 0,
            "answer_relevance": 0,
            "context_relevance": 0,
            "correctness": 0,
            "overall_score": 0,
            "explanation": f"Evaluation error: {str(e)}"
        }

def process_model_answers(df, model_column, model_name):
    """
    Process and evaluate answers for a specific model
    """
    
    results = []
    
    print(f"Starting to process {model_name} answers - {len(df)} rows...")
    
    for index, row in df.iterrows():
        print(f"Processing {model_name} - row {index + 1}/{len(df)}")
        
        # Extract data
        category = row['Category']
        question = row['Questions']
        golden_answer = row['Golden Answers']
        model_answer = row[model_column]
        context = row['Context']
        
        # Evaluate answer
        evaluation = evaluate_model_answer(
            category, question, golden_answer, model_answer, context, model_name
        )
        
        # Add result
        result_row = {
            'Category': category,
            'Questions': question,
            'Golden Answers': golden_answer,
            f'{model_name} Answer': model_answer,
            'Context': context,
            'Faithfulness Score': evaluation['faithfulness'],
            'Answer Relevance Score': evaluation['answer_relevance'],
            'Context Relevance Score': evaluation['context_relevance'],
            'correctness Score': evaluation['correctness'],
            'Overall Score': evaluation['overall_score'],
            'Evaluation Explanation': evaluation['explanation']
        }
        
        results.append(result_row)
        
        # Short pause to avoid API rate limits
        time.sleep(1)
    
    return results

def create_evaluation_report(results, output_file, model_name):
    """
    Create evaluation report and save it
    """
    
    # Create DataFrame from results
    results_df = pd.DataFrame(results)
    
    # Save results to Excel file
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Main table
        results_df.to_excel(writer, sheet_name='Detailed Evaluation', index=False)
        
        # Summary statistics
        summary_stats = {
            'Metric': ['Faithfulness', 'Answer Relevance', 'Context Relevance', 'correctness' , 'Overall Score'],
            'Average Score': [
                results_df['Faithfulness Score'].mean(),
                results_df['Answer Relevance Score'].mean(),
                results_df['Context Relevance Score'].mean(),
                results_df['correctness Score'].mean(),
                results_df['Overall Score'].mean()
            ],
            'Min Score': [
                results_df['Faithfulness Score'].min(),
                results_df['Answer Relevance Score'].min(),
                results_df['Context Relevance Score'].min(),
                results_df['correctness Score'].min(),
                results_df['Overall Score'].min()
            ],
            'Max Score': [
                results_df['Faithfulness Score'].max(),
                results_df['Answer Relevance Score'].max(),
                results_df['Context Relevance Score'].max(),
                results_df['correctness Score'].max(),
                results_df['Overall Score'].max()
            ]
        }
        
        summary_df = pd.DataFrame(summary_stats)
        summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)
        
        # Evaluation by category
        category_stats = results_df.groupby('Category').agg({
            'Faithfulness Score': 'mean',
            'Answer Relevance Score': 'mean',
            'Context Relevance Score': 'mean',
            'correctness Score': 'mean',
            'Overall Score': 'mean'
        }).round(2)
        
        category_stats.to_excel(writer, sheet_name='Category Analysis')
    
    print(f"{model_name} report saved to: {output_file}")
    
    # Print quick summary
    print(f"\n=== {model_name} Results Summary ===")
    print(f"Average Faithfulness Score: {results_df['Faithfulness Score'].mean():.2f}")
    print(f"Average Answer Relevance Score: {results_df['Answer Relevance Score'].mean():.2f}")
    print(f"Average Context Relevance Score: {results_df['Context Relevance Score'].mean():.2f}")
    print(f"Average correctness Score: {results_df['correctness Score'].mean():.2f}")
    print(f"Average Overall Score: {results_df['Overall Score'].mean():.2f}")

def create_comparison_report(all_results, output_file):
    """
    Create a comparison report across all models
    """
    
    comparison_data = []
    
    for model_name, results in all_results.items():
        results_df = pd.DataFrame(results)
        
        # Calculate averages for each category
        category_averages = results_df.groupby('Category').agg({
            'Faithfulness Score': 'mean',
            'Answer Relevance Score': 'mean',
            'Context Relevance Score': 'mean',
            'correctness Score': 'mean',
            'Overall Score': 'mean'
        }).round(2)
        
        # Add model name and overall averages
        for category in category_averages.index:
            comparison_data.append({
                'Model': model_name,
                'Category': category,
                'Faithfulness': category_averages.loc[category, 'Faithfulness Score'],
                'Answer Relevance': category_averages.loc[category, 'Answer Relevance Score'],
                'Context Relevance': category_averages.loc[category, 'Context Relevance Score'],
                'correctness': category_averages.loc[category, 'correctness Score'],
                'Overall Score': category_averages.loc[category, 'Overall Score']
            })
        
        # Add overall average across all categories
        comparison_data.append({
            'Model': model_name,
            'Category': 'OVERALL',
            'Faithfulness': results_df['Faithfulness Score'].mean(),
            'Answer Relevance': results_df['Answer Relevance Score'].mean(),
            'Context Relevance': results_df['Context Relevance Score'].mean(),
            'correctness': results_df['correctness Score'].mean(),
            'Overall Score': results_df['Overall Score'].mean()
        })
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Save comparison report
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        comparison_df.to_excel(writer, sheet_name='Model Comparison', index=False)
        
        # Create pivot tables for better visualization
        pivot_faithfulness = comparison_df.pivot(index='Category', columns='Model', values='Faithfulness')
        pivot_relevance = comparison_df.pivot(index='Category', columns='Model', values='Answer Relevance')
        pivot_context = comparison_df.pivot(index='Category', columns='Model', values='Context Relevance')
        pivot_correctness = comparison_df.pivot(index='Category', columns='Model', values='correctness')
        pivot_overall = comparison_df.pivot(index='Category', columns='Model', values='Overall Score')
        
        pivot_faithfulness.to_excel(writer, sheet_name='Faithfulness Comparison')
        pivot_relevance.to_excel(writer, sheet_name='Answer Relevance Comparison')
        pivot_context.to_excel(writer, sheet_name='Context Relevance Comparison')
        pivot_correctness.to_excel(writer, sheet_name='correctness Comparison')
        pivot_overall.to_excel(writer, sheet_name='Overall Score Comparison')
    
    print(f"Comparison report saved to: {output_file}")








def main():
    """
    Main function
    """
    
    # Input Excel file path
    input_file = "../middleFiles/results_with_all_contexts.xlsx"
    
    # Define models to evaluate
    models_config = {
        'gpt-4o': 'gpt-4o',
        'DeepSeek Chat': 'DeepSeek Chat', 
        'Claude3.7': 'Claude3.7',
        'Gemini2.5Pro': 'Gemini2.5Pro',
        'Grok3': 'Grok3'
    }
    
    try:
        print("Starting evaluation process for all models...")
        
        # Read the input file once
        df = pd.read_excel(input_file)
        print(f"Loaded {len(df)} rows from {input_file}")
        
        # Store all results for comparison
        all_results = {}
        
        # Process each model
        for model_name, column_name in models_config.items():
            print(f"\n{'='*50}")
            print(f"Processing {model_name}...")
            print(f"{'='*50}")
            
            # Check if column exists
            if column_name not in df.columns:
                print(f"Warning: Column '{column_name}' not found in the data. Skipping {model_name}.")
                continue
            
            # Process model answers
            results = process_model_answers(df, column_name, model_name)
            
            # Store results for comparison
            all_results[model_name] = results
            
            # Create individual report
            output_file = f"../outputFiles/{model_name.lower()}_evaluation_results.xlsx"
            create_evaluation_report(results, output_file, model_name)
            
            print(f"{model_name} evaluation completed!")
        
        # Create comparison report
        if all_results:
            print(f"\n{'='*50}")
            print("Creating comparison report...")
            print(f"{'='*50}")
            create_comparison_report(all_results, "../outputFiles/models_comparison_report.xlsx")
        
        print("\nAll evaluations completed successfully!")
        print(f"Generated files:")
        for model_name in all_results.keys():
            print(f"- {model_name.lower()}_evaluation_results.xlsx")
        print("- models_comparison_report.xlsx")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
