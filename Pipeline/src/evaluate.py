def ExtractBaseName(filename):
    a = filename.split('_')
    # print(a)
    name = a[0]
    return name

def EvaluateMatches(groups):
    matches = {}
    total_correct = total_matches = 0
    
    for ref, matches_list in tqdm(groups.items(), desc="Evaluating matches"):
        ref_base = ExtractBaseName(ref)
        relevant_matches = matches_list[1:]  # Exclude self-match
        correct = sum(1 for m in relevant_matches if ExtractBaseName(m) == ref_base)
        total_attempted = len(relevant_matches)
        accuracy = (correct / total_attempted * 100) if total_attempted else 0
        
        matches[ref] = {
            'accuracy': accuracy,
            'correct_matches': correct,
            'total_matches': total_attempted,
            'matches': relevant_matches,
            'reference_name': ref_base
        }
        total_correct += correct
        total_matches += total_attempted
    
    person_accuracies = defaultdict(list)
    for ref, data in matches.items():
        person_accuracies[ExtractBaseName(ref)].append(data['accuracy'])
    
    metrics = {
        'overall_accuracy': (total_correct / total_matches * 100) if total_matches else 0,
        'per_image_accuracies': matches,
        'person_accuracies': {p: sum(acc)/len(acc) for p, acc in person_accuracies.items()},
        'total_correct': total_correct,
        'total_matches': total_matches,
        'total_images': len(groups)
    }
    
    return metrics

def PrintEvaluationReport(metrics):
    print("\n=== Face Matching Evaluation Report ===")
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.2f}%")
    print(f"Total Images: {metrics['total_images']}")
    print(f"Total Correct Matches: {metrics['total_correct']}")
    print(f"Total Matches Attempted: {metrics['total_matches']}")
    
    print("\nDetailed Match Examples:")
    for ref, data in list(metrics['per_image_accuracies'].items())[:5]:
        print(f"\nReference: {ref}")
        print(f"Accuracy: {data['accuracy']:.2f}%")
        print("Matches:")
        for match in data['matches']:
            is_correct = ExtractBaseName(match) == data['reference_name']
            status = "✓" if is_correct else "✗"
            print(f"  {status} {match}")