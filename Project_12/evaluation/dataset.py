dataset = [
    # --- General Psychiatry & Diagnostics ---
    {
        "question": "What is the primary difference between Schizophrenia and Schizophreniform disorder?",
        "ground_truth": "The primary difference is the duration of symptoms. Schizophreniform disorder lasts between 1 and 6 months, whereas Schizophrenia requires continuous signs of the disturbance for at least 6 months."
    },
    {
        "question": "What are the positive symptoms of schizophrenia?",
        "ground_truth": "Positive symptoms include hallucinations, delusions, disorganized thinking (speech), and grossly disorganized or abnormal motor behavior (including catatonia)."
    },
    {
        "question": "How is Bipolar I disorder distinguished from Bipolar II disorder?",
        "ground_truth": "Bipolar I disorder involves at least one manic episode, whereas Bipolar II disorder involves at least one hypomanic episode and at least one major depressive episode, with no history of a full manic episode."
    },
    {
        "question": "What is the duration requirement for diagnosing Generalized Anxiety Disorder (GAD)?",
        "ground_truth": "Excessive anxiety and worry must occur more days than not for at least 6 months."
    },
    {
        "question": "What distinguishes Post-Traumatic Stress Disorder (PTSD) from Acute Stress Disorder?",
        "ground_truth": "Acute Stress Disorder is diagnosed when symptoms occur within the first month after the trauma. If symptoms persist for more than one month, the diagnosis is changed to PTSD."
    },
    {
        "question": "What are the core features of Obsessive-Compulsive Disorder (OCD)?",
        "ground_truth": "The core features are the presence of obsessions (recurrent, intrusive thoughts or urges) and/or compulsions (repetitive behaviors or mental acts performed in response to an obsession)."
    },
    {
        "question": "What is the hallmark cognitive deficit in delirium?",
        "ground_truth": "The hallmark is a disturbance in attention and awareness that develops over a short period of time and tends to fluctuate in severity during the course of a day."
    },
    {
        "question": "How does vascular dementia differ from Alzheimer's disease in its onset?",
        "ground_truth": "Vascular dementia typically has a sudden onset and a stepwise progression of cognitive decline, often linked to cerebrovascular events, whereas Alzheimer's has a gradual, insidious onset and continuous decline."
    },
    {
        "question": "What are the characteristics of Cluster B personality disorders?",
        "ground_truth": "Cluster B personality disorders are characterized by dramatic, overly emotional, or unpredictable thinking or behavior. They include antisocial, borderline, histrionic, and narcissistic personality disorders."
    },
    {
        "question": "What is the main feature of Factitious Disorder?",
        "ground_truth": "The intentional production or feigning of physical or psychological signs or symptoms, without obvious external rewards, to assume the sick role."
    },

    # --- Child and Adolescent Psychiatry ---
    {
        "question": "What are the three main symptom presentations of ADHD?",
        "ground_truth": "The three presentations are predominantly inattentive, predominantly hyperactive-impulsive, and combined presentation."
    },
    {
        "question": "What are the core diagnostic domains for Autism Spectrum Disorder (ASD)?",
        "ground_truth": "Persistent deficits in social communication and social interaction, and restricted, repetitive patterns of behavior, interests, or activities."
    },
    {
        "question": "How does Oppositional Defiant Disorder (ODD) differ from Conduct Disorder (CD)?",
        "ground_truth": "ODD involves a pattern of angry/irritable mood and defiant behavior, but unlike CD, it does not typically involve serious violations of societal norms, basic rights of others, or aggressive acts towards people or animals."
    },
    {
        "question": "What is Separation Anxiety Disorder in children?",
        "ground_truth": "It is developmentally inappropriate and excessive fear or anxiety concerning separation from those to whom the individual is attached."
    },
    {
        "question": "What are the criteria for diagnosing Tourette's Disorder?",
        "ground_truth": "The presence of both multiple motor tics and one or more vocal tics for more than 1 year, with onset before age 18."
    },
    {
        "question": "What is Selective Mutism?",
        "ground_truth": "A consistent failure to speak in specific social situations where there is an expectation for speaking, despite speaking in other situations."
    },
    {
        "question": "What is Enuresis?",
        "ground_truth": "Repeated voiding of urine into bed or clothes, whether involuntary or intentional, in a child who is at least 5 years of age chronologically."
    },
    {
        "question": "What is the recommended first-line treatment for mild to moderate depression in adolescents?",
        "ground_truth": "Psychological therapies, such as Cognitive Behavioral Therapy (CBT) or Interpersonal Therapy (IPT), are generally recommended as first-line treatments."
    },
    {
        "question": "What are the typical signs of anorexia nervosa in adolescents?",
        "ground_truth": "Restriction of energy intake leading to significantly low body weight, intense fear of gaining weight, and a distorted perception of body weight or shape."
    },
    {
        "question": "What is the difference between specific learning disorder and intellectual disability?",
        "ground_truth": "Specific learning disorder involves difficulties learning and using specific academic skills despite normal overall intelligence, whereas intellectual disability involves generalized deficits in intellectual and adaptive functioning."
    },

    # --- Forensic Psychiatry ---
    {
        "question": "What does 'competence to stand trial' mean?",
        "ground_truth": "It refers to a defendant's current ability to understand the nature of the criminal proceedings against them and to assist their attorney in their own defense."
    },
    {
        "question": "What is the McNaughten Rule in the context of the insanity defense?",
        "ground_truth": "It is a legal standard stating that a defendant is not guilty by reason of insanity if, at the time of the act, a mental disease or defect prevented them from knowing the nature and quality of the act or knowing that the act was wrong."
    },
    {
        "question": "What is the Tarasoff rule (Duty to Warn/Protect)?",
        "ground_truth": "It is a legal obligation for a mental health professional to breach confidentiality and take reasonable steps to protect an identifiable third party if a patient presents a serious danger of violence to that person."
    },
    {
        "question": "What is malingering?",
        "ground_truth": "The intentional production of false or grossly exaggerated physical or psychological symptoms, motivated by external incentives such as avoiding military duty, avoiding work, obtaining financial compensation, or evading criminal prosecution."
    },
    {
        "question": "What constitutes 'testamentary capacity'?",
        "ground_truth": "The mental capacity required to make a valid will, which includes knowing what a will is, knowing the nature and extent of one's property, and knowing the natural objects of one's bounty (e.g., family members)."
    },
    {
        "question": "What are the common criteria for involuntary psychiatric commitment?",
        "ground_truth": "The individual must have a mental illness and, as a result, be a danger to themselves, a danger to others, or gravely disabled (unable to provide for basic personal needs)."
    },
    {
        "question": "What is 'mens rea'?",
        "ground_truth": "A legal concept meaning 'guilty mind,' referring to the mental state or intent required to be convicted of a crime."
    },
    {
        "question": "How does forensic psychiatry differ from clinical psychiatry?",
        "ground_truth": "Clinical psychiatry focuses on diagnosing and treating patients, whereas forensic psychiatry focuses on addressing legal questions and providing expert opinions for the court, with the court (not the patient) often being the client."
    },
    {
        "question": "What is factitious disorder imposed on another (Munchausen syndrome by proxy)?",
        "ground_truth": "It involves falsifying or inducing physical or psychological signs or symptoms in another person (usually a child by a caregiver), associated with identified deception, without obvious external rewards."
    },
    {
        "question": "What is the role of a forensic psychiatrist in personal injury cases?",
        "ground_truth": "To evaluate the plaintiff's mental state to determine if psychological harm occurred as a direct result of the specific injury or event in question."
    },

    # --- Psychopharmacology & Treatments ---
    {
        "question": "What is Neuroleptic Malignant Syndrome (NMS)?",
        "ground_truth": "A rare but life-threatening idiosyncratic reaction to antipsychotic drugs characterized by fever, severe muscle rigidity, altered mental status, and autonomic instability."
    },
    {
        "question": "What is the primary risk associated with Clozapine?",
        "ground_truth": "Agranulocytosis, a severe and potentially fatal drop in white blood cell count, requiring strict blood monitoring."
    },
    {
        "question": "What are the common side effects of SSRIs?",
        "ground_truth": "Common side effects include gastrointestinal disturbances (nausea, diarrhea), sexual dysfunction, insomnia, and weight changes."
    },
    {
        "question": "Why must patients taking MAOIs avoid tyramine-rich foods?",
        "ground_truth": "Consuming tyramine-rich foods while on MAOIs can cause a hypertensive crisis, a severe and potentially fatal spike in blood pressure."
    },
    {
        "question": "What is the therapeutic index of Lithium?",
        "ground_truth": "Lithium has a narrow therapeutic index, meaning the dose required for therapeutic effect is close to the dose that causes toxicity. Regular blood level monitoring is required."
    },
    {
        "question": "What are symptoms of Lithium toxicity?",
        "ground_truth": "Symptoms include severe nausea and vomiting, coarse hand tremor, ataxia, confusion, and in severe cases, seizures and coma."
    },
    {
        "question": "What is Tardive Dyskinesia?",
        "ground_truth": "A delayed side effect of long-term use of dopamine antagonist medications (antipsychotics), characterized by involuntary, repetitive body movements, most often of the face, lips, and tongue."
    },
    {
        "question": "What is Serotonin Syndrome?",
        "ground_truth": "A potentially life-threatening condition caused by excessive serotonergic activity in the nervous system, characterized by altered mental status, autonomic hyperactivity, and neuromuscular abnormalities (e.g., clonus)."
    },
    {
        "question": "How does the mechanism of action of typical antipsychotics differ from atypical antipsychotics?",
        "ground_truth": "Typical antipsychotics primarily block dopamine D2 receptors, while atypical antipsychotics block both dopamine D2 receptors and serotonin 5-HT2A receptors."
    },
    {
        "question": "What is the role of benzodiazepines in the treatment of anxiety?",
        "ground_truth": "Benzodiazepines enhance the effect of the neurotransmitter GABA, providing rapid, short-term relief of severe anxiety symptoms, but carry a risk of tolerance and dependence."
    },

    # --- Deep Dives & Edge Cases ---
    {
        "question": "What is somatic symptom disorder?",
        "ground_truth": "A condition characterized by one or more somatic symptoms that are distressing or result in significant disruption of daily life, accompanied by excessive thoughts, feelings, or behaviors related to the symptoms."
    },
    {
        "question": "What is the difference between a hypnagogic and a hypnopompic hallucination?",
        "ground_truth": "Hypnagogic hallucinations occur while falling asleep, whereas hypnopompic hallucinations occur while waking up."
    },
    {
        "question": "What is cyclothymic disorder?",
        "ground_truth": "A mood disorder characterized by chronic, fluctuating mood disturbances involving numerous periods of hypomanic symptoms and numerous periods of depressive symptoms that do not meet full criteria for hypomania or major depression, lasting for at least 2 years."
    },
    {
        "question": "What characterizes borderline personality disorder?",
        "ground_truth": "A pervasive pattern of instability in interpersonal relationships, self-image, and affects, along with marked impulsivity."
    },
    {
        "question": "What is dissociative amnesia?",
        "ground_truth": "An inability to recall important autobiographical information, usually of a traumatic or stressful nature, that is inconsistent with ordinary forgetting."
    },
    {
        "question": "What is agoraphobia?",
        "ground_truth": "Marked fear or anxiety about situations from which escape might be difficult or help might not be available in the event of developing panic-like symptoms or other incapacitating symptoms (e.g., using public transportation, being in open spaces)."
    },
    {
        "question": "What distinguishes schizoaffective disorder from schizophrenia?",
        "ground_truth": "Schizoaffective disorder features a major mood episode (depressive or manic) concurrent with the active phase symptoms of schizophrenia, along with at least 2 weeks of delusions or hallucinations in the absence of a major mood episode."
    },
    {
        "question": "What are the key features of narcolepsy?",
        "ground_truth": "Recurrent periods of an irrepressible need to sleep, lapsing into sleep, or napping occurring within the same day, often accompanied by cataplexy, hypocretin deficiency, or specific REM sleep abnormalities."
    },
    {
        "question": "What is body dysmorphic disorder?",
        "ground_truth": "Preoccupation with one or more perceived defects or flaws in physical appearance that are not observable or appear slight to others, accompanied by repetitive behaviors or mental acts in response to the appearance concerns."
    },
    {
        "question": "What is the primary goal of cognitive behavioral therapy (CBT) for depression?",
        "ground_truth": "To identify and modify negative, distorted thought patterns and behaviors that contribute to and maintain depressed mood."
    }
]