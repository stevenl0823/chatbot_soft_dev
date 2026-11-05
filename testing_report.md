# AI-Assisted Software Testing Report

**Student Name:** ______Wang Liao________________________  
**Date:** _____10/6/26_______________

This is an individual report based on your own Week 3 RAG chatbot.


## 1. Requirements and Test Oracle
- What behaviors did you decide were required?
The chatbot should answer questions directly using relevant information from the indexed reports, preserve reported numbers and ranges accurately, and show the source report and page for its evidence. It should handle paraphrased questions consistently, reject false premises rather than repeat them, ask for clarification when a question is too broad, and abstain when the reports do not contain the answer. Empty questions should be rejected. For multi-part questions, the answer should address each requested part and keep the response organized.
- What source material was used as ground truth?
Expected facts and page references came from the PDFs in the project’s document collection, recorded in test_cases.json.
## 2. AI-Generated Test Cases
- Which tests came from requirements?
- Which tests were suggested by AI?
- Which AI suggestion relied on an invented assumption?
Pytest is coming from AI suggestion. At the first time when I implemented the Pytest as what the requirement instructed, it did not perform effectively, so I had to redo it at the later stages when there were issues in the quality of the outputs. At this time, AI suggested me to do another round of Pytest, which corrected some issues in the original files, which were not identified in the first round of testing. Everything else were performed under the known requirements, including the stress tests and performance tests. 
The AI-generated tests assumed the local test-case schema matched a template. I should have checked the actual JSON keys and types before using those tests.
## 3. Functional Test Results
- Number passed / failed:
- Most important failure:
1 failed, 24 passed in 14.23s. the most important failure comes from the assertion error. 
## 4. Performance Results
- Min / average / median / max latency:
- Proposed target and justification:
minimum latency :0.00s,
average latency : 1.21s
median latency : 0.01s
max latency : 12.03s
failed requests 0 of 10
based on the performance, no justification is needed. 
## 5. Stress / Concurrency Results
- What changed at 1, 3, and 5 simultaneous requests?
At 1 concurrent request, 1/1 succeeded; latency was 12.22 s, including the initial PDF indexing. At 3 concurrent requests, 3/3 succeeded, averaging 0.01 s with 0.02 s total wall time. At 5 concurrent requests, 5/5 succeeded, averaging 0.01 s with 0.03 s total wall time.
No failures or API/rate-limit errors occurred, and the app remained stable. The 3- and 5-request runs used the already-warmed index, so their latencies aren’t a cold-start comparison.
## 6. User Acceptance Testing
Ask one classmate to test your chatbot for approximately five minutes; record that classmate’s ratings and comments below.
- Relevance rating:5
- Correctness rating:5
- Clarity rating:5
- Trust rating:5
- Overall usefulness:5
- User comments:The chatbot worked well and it gave clear answers. The first response took longer while the PDFs loaded, but later answers were faster. 

## 7. Failure Analysis
Describe at least three failures or weak outcomes and classify each as retrieval, generation, specification/oracle, weak assertion, hallucinated test scenario, or performance/rate-limit issue.
Generation: The generation mode was the stage that I faced the most failures. The initial version of the chatbot passed all the previous tests, including the stress test and performance test. However, when I ask the sample questions, it returned with answers along with unnecessary content retrieved from the PDF. The AI agent checked the issue and reported that the issue actually came from the original PDF file. It says: PDF extraction was flattening line breaks, and the answer logic could return noisy or weakly matched text. I believe when the issue is coming from the extraction of the original file, the stress test and performance test would have difficulties identifying the issues. 
Retrieval: The multi-part evaluation question initially retrieved a passage about security use cases rather than the relevant reported benefits and concern. This showed that general similarity ranking did not reliably find evidence for every part of a compound question.
Performance: The first request took about 12 seconds because it included PDF loading and indexing, but later warm requests were about 0.01 seconds. No requests failed and no rate-limit errors occurred.
## 8. Reflection
Would you trust the same model that helps write the chatbot to be the sole generator/judge of its tests? What would you change before production use?
No. they are asking the same questions and there’s lack of diversity. It may repeat the assumptions and blind spots it introduced while building the chatbot, creating tests that overlook important failures. I would combine its tests with independently written cases, human-reviewed expected answers, and automated checks for requirements such as factual accuracy, output format, and privacy.
I would change the user interface, graphic design and other customization sections before put into production. As AI software developers, finishing the development of the application and successfully testing it are only the fundamental stage. We need to collect more user feedback by implementing A/B testing and improve it before the production stage
