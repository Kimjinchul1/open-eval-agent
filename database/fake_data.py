import json
import os
import random
from typing import Dict, List, Any
import uuid

class FakeDatasetGenerator:
    def __init__(self):
        # 모델 목록
        self.models = [
            'deepseek-r1', 'deepseek-v3', 'llama-4', 'gpt-4o', 'claude-3.5-sonnet',
            'qwen-max', 'gemini-pro', 'llama-3.1-405b', 'mistral-large', 'llama-4-Maverick', 'llama-4-Scout', 'GaussO-Think', 'GaussO-Think-Ultra',
            'KIMI-K2', 'KIMI-K2-AWQ']
        
        # 벤치마크 목록 (새로운 벤치마크 추가)
        self.benchmarks = ['aime', 'mmlu', 'mmlu-redux', 'mmlu-pro', 'math500', 'ds-mmlu', 'hle']
        
        # 난이도 레벨
        self.difficulties = ['Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme']
        
        # 비즈니스 카테고리 (오타 포함해서 원본과 일치시킴)
        self.business_categories = [
            'Memory', 'Reasoning', 'Mathematics', 'Science', 'History',
            'Literature', 'Philosophy', 'Logic', 'Physics', 'Chemistry'
        ]
        
        # MMLU 서브젝트
        self.mmlu_subjects = [
            'abstract_algebra', 'anatomy', 'astronomy', 'business_ethics',
            'clinical_knowledge', 'college_biology', 'college_chemistry',
            'college_computer_science', 'college_mathematics', 'college_medicine',
            'college_physics', 'computer_security', 'conceptual_physics',
            'econometrics', 'electrical_engineering', 'elementary_mathematics',
            'formal_logic', 'global_facts', 'high_school_biology',
            'high_school_chemistry', 'high_school_computer_science',
            'high_school_european_history', 'high_school_geography',
            'high_school_government_and_politics', 'high_school_macroeconomics',
            'high_school_mathematics', 'high_school_microeconomics',
            'high_school_physics', 'high_school_psychology',
            'high_school_statistics', 'high_school_us_history',
            'high_school_world_history', 'human_aging', 'human_sexuality',
            'international_law', 'jurisprudence', 'logical_fallacies',
            'machine_learning', 'management', 'marketing', 'medical_genetics',
            'miscellaneous', 'moral_disputes', 'moral_scenarios', 'nutrition',
            'philosophy', 'prehistory', 'professional_accounting',
            'professional_law', 'professional_medicine', 'professional_psychology',
            'public_relations', 'security_studies', 'sociology', 'us_foreign_policy',
            'virology', 'world_religions'
        ]
        
        # DS-MMLU 반도체 특화 서브젝트
        self.dsmmlu_subjects = [
            'semiconductor_physics', 'device_fabrication', 'lithography',
            'etching_processes', 'thin_film_deposition', 'ion_implantation',
            'cmos_design', 'analog_circuit_design', 'digital_circuit_design',
            'memory_technology', 'power_semiconductor', 'rf_semiconductor',
            'quantum_devices', 'optoelectronics', 'mems_technology',
            'packaging_technology', 'yield_analysis', 'process_integration',
            'contamination_control', 'metrology_inspection', 'failure_analysis',
            'reliability_testing', 'esd_protection', 'thermal_management'
        ]
        
        # HLE 카테고리
        self.hle_categories = [
            'Existential Philosophy', 'Advanced Mathematics', 'Quantum Physics',
            'Consciousness Studies', 'Artificial Intelligence Ethics', 'Cosmology',
            'Evolutionary Biology', 'Complexity Theory', 'Information Theory',
            'Game Theory', 'Meta-Ethics', 'Philosophy of Mind'
        ]
        
        # 모델별 성능 프로필 정의
        self.model_performance = {
            # 최상위 티어 모델들 (85-95% 기본 성능)
            'deepseek-r1': {'base': 0.92, 'math_bonus': 0.08, 'reasoning_bonus': 0.05, 'knowledge_penalty': 0.02},
            'gpt-4o': {'base': 0.89, 'math_bonus': 0.04, 'reasoning_bonus': 0.06, 'knowledge_penalty': 0.01},
            'claude-3.5-sonnet': {'base': 0.87, 'math_bonus': 0.02, 'reasoning_bonus': 0.08, 'knowledge_penalty': 0.01},
            
            # 상위 티어 모델들 (75-85% 기본 성능) 
            'llama-4': {'base': 0.82, 'math_bonus': 0.05, 'reasoning_bonus': 0.03, 'knowledge_penalty': 0.02},
            'deepseek-v3': {'base': 0.80, 'math_bonus': 0.07, 'reasoning_bonus': 0.04, 'knowledge_penalty': 0.03},
            'GaussO-Think-Ultra': {'base': 0.79, 'math_bonus': 0.09, 'reasoning_bonus': 0.06, 'knowledge_penalty': 0.04},
            'qwen-max': {'base': 0.77, 'math_bonus': 0.03, 'reasoning_bonus': 0.02, 'knowledge_penalty': 0.02},
            
            # 중상위 티어 모델들 (65-75% 기본 성능)
            'llama-4-Maverick': {'base': 0.74, 'math_bonus': 0.06, 'reasoning_bonus': 0.04, 'knowledge_penalty': 0.03},
            'gemini-pro': {'base': 0.72, 'math_bonus': 0.02, 'reasoning_bonus': 0.03, 'knowledge_penalty': 0.03},
            'GaussO-Think': {'base': 0.70, 'math_bonus': 0.08, 'reasoning_bonus': 0.05, 'knowledge_penalty': 0.05},
            'llama-3.1-405b': {'base': 0.68, 'math_bonus': 0.04, 'reasoning_bonus': 0.02, 'knowledge_penalty': 0.04},
            
            # 중위 티어 모델들 (55-65% 기본 성능)
            'mistral-large': {'base': 0.62, 'math_bonus': 0.05, 'reasoning_bonus': 0.03, 'knowledge_penalty': 0.05},
            'llama-4-Scout': {'base': 0.58, 'math_bonus': 0.07, 'reasoning_bonus': 0.04, 'knowledge_penalty': 0.06},
            'KIMI-K2': {'base': 0.55, 'math_bonus': 0.03, 'reasoning_bonus': 0.02, 'knowledge_penalty': 0.07},
            'KIMI-K2-AWQ': {'base': 0.52, 'math_bonus': 0.02, 'reasoning_bonus': 0.01, 'knowledge_penalty': 0.08},
        }
        
        # 벤치마크별 특성 정의
        self.benchmark_characteristics = {
            'aime': {'type': 'math', 'difficulty_factor': 1.3, 'variance': 0.15},
            'math500': {'type': 'math', 'difficulty_factor': 1.2, 'variance': 0.12},
            'mmlu': {'type': 'knowledge', 'difficulty_factor': 0.9, 'variance': 0.08},
            'mmlu-redux': {'type': 'knowledge', 'difficulty_factor': 0.95, 'variance': 0.10},
            'mmlu-pro': {'type': 'knowledge', 'difficulty_factor': 1.1, 'variance': 0.13},
            'ds-mmlu': {'type': 'specialized_knowledge', 'difficulty_factor': 1.4, 'variance': 0.18},
            'hle': {'type': 'reasoning', 'difficulty_factor': 1.8, 'variance': 0.25}
        }

    def get_model_performance(self, model: str, benchmark: str) -> float:
        """모델과 벤치마크에 따른 성능 점수 계산"""
        if model not in self.model_performance:
            # 알려지지 않은 모델은 중간 성능으로 설정
            base_perf = random.uniform(0.4, 0.7)
        else:
            profile = self.model_performance[model]
            base_perf = profile['base']
            
            # 벤치마크 타입에 따른 보정
            bench_char = self.benchmark_characteristics.get(benchmark, {'type': 'knowledge', 'difficulty_factor': 1.0, 'variance': 0.1})
            
            if bench_char['type'] == 'math':
                base_perf += profile['math_bonus']
            elif bench_char['type'] == 'reasoning':
                base_perf += profile['reasoning_bonus'] 
            elif bench_char['type'] == 'knowledge' or bench_char['type'] == 'specialized_knowledge':
                base_perf -= profile['knowledge_penalty']
            
            # 난이도 팩터 적용
            base_perf = base_perf / bench_char['difficulty_factor']
            
            # 분산 추가 (모델별 일관성 차이)
            variance = bench_char['variance']
            performance_noise = random.gauss(0, variance)
            base_perf += performance_noise
        
        # 0과 1 사이로 클리핑하되, 일부 모델은 매우 낮은 성능도 허용
        return max(0.05, min(0.98, base_perf))

    def generate_question_by_benchmark(self, benchmark: str) -> Dict[str, Any]:
        """벤치마크별로 적절한 질문 생성"""
        if benchmark == 'aime':
            return self._generate_aime_question()
        elif benchmark in ['mmlu', 'mmlu-redux', 'mmlu-pro']:
            return self._generate_mmlu_question()
        elif benchmark == 'math500':
            return self._generate_math_question()
        elif benchmark == 'ds-mmlu':
            return self._generate_dsmmlu_question()
        elif benchmark == 'hle':
            return self._generate_hle_question()
        else:
            return self._generate_generic_question()

    def _generate_aime_question(self) -> Dict[str, Any]:
        """AIME 스타일 수학 문제 생성"""
        questions = [
            "Find the number of positive integers n ≤ 1000 such that gcd(n, 2024) = 1.",
            "Let f(x) = x³ - 3x² + 2x - 1. Find the sum of all real roots of f(x) = 0.",
            "In triangle ABC, AB = 13, BC = 14, CA = 15. Find the length of the median from A to BC.",
            "Find the remainder when 2²⁰²⁴ is divided by 1000.",
            "How many ways can 8 people sit around a circular table if 3 specific people must sit together?",
            "Find the coefficient of x¹⁰ in the expansion of (1 + x + x²)⁸.",
            "Let S = 1 + 1/2 + 1/3 + ... + 1/100. Find the largest integer k such that S > k/100.",
            "In how many ways can we arrange the letters in MATHEMATICS?",
            "Find the area of the region bounded by y = x², y = 2x, and x = 3.",
            "Solve for x: log₂(x + 1) + log₂(x - 1) = 3."
        ]
        
        question = random.choice(questions)
        answer = random.randint(0, 999)  # AIME answers are 0-999
        
        return {
            'question': question,
            'Answer': str(answer),
            'answer_type': 'numeric'
        }

    def _generate_mmlu_question(self) -> Dict[str, Any]:
        """MMLU 스타일 객관식 문제 생성"""
        questions = [
            {
                'question': "Which of the following is NOT a characteristic of prokaryotic cells?",
                'choices': {
                    'A': "Lack of membrane-bound nucleus",
                    'B': "Presence of ribosomes", 
                    'C': "Presence of mitochondria",
                    'D': "Circular DNA"
                },
                'answer': 'C'
            },
            {
                'question': "What is the derivative of f(x) = x³ + 2x² - 5x + 1?",
                'choices': {
                    'A': "3x² + 4x - 5",
                    'B': "3x² + 2x - 5",
                    'C': "x³ + 4x - 5",
                    'D': "3x² + 4x - 1"
                },
                'answer': 'A'
            },
            {
                'question': "Which economic theory suggests that government spending can stimulate economic growth during recessions?",
                'choices': {
                    'A': "Classical economics",
                    'B': "Keynesian economics",
                    'C': "Supply-side economics", 
                    'D': "Monetarism"
                },
                'answer': 'B'
            },
            {
                'question': "In computer science, what does 'Big O' notation describe?",
                'choices': {
                    'A': "Memory usage of algorithms",
                    'B': "Time complexity of algorithms",
                    'C': "Both time and space complexity",
                    'D': "Code readability"
                },
                'answer': 'C'
            },
            {
                'question': "Who wrote the novel '1984'?",
                'choices': {
                    'A': "Aldous Huxley",
                    'B': "Ray Bradbury",
                    'C': "George Orwell",
                    'D': "Isaac Asimov"
                },
                'answer': 'C'
            }
        ]
        
        q_data = random.choice(questions)
        return {
            'question': q_data['question'],
            'Answer': q_data['answer'],
            'A': q_data['choices']['A'],
            'B': q_data['choices']['B'], 
            'C': q_data['choices']['C'],
            'D': q_data['choices']['D'],
            'answer_type': 'multiple_choice'
        }

    def _generate_dsmmlu_question(self) -> Dict[str, Any]:
        """DS-MMLU 반도체 특화 객관식 문제 생성"""
        questions = [
            {
                'question': "In CMOS technology, what is the primary purpose of the well implantation step?",
                'choices': {
                    'A': "To create source/drain regions",
                    'B': "To form the gate oxide",
                    'C': "To establish the substrate doping for opposite polarity devices",
                    'D': "To create metal interconnects"
                },
                'answer': 'C'
            },
            {
                'question': "What is the main advantage of FinFET technology over planar MOSFET?",
                'choices': {
                    'A': "Lower manufacturing cost",
                    'B': "Better short channel effect control",
                    'C': "Simpler design rules",
                    'D': "Higher operating voltage"
                },
                'answer': 'B'
            },
            {
                'question': "In photolithography, what does the term 'critical dimension' refer to?",
                'choices': {
                    'A': "The thickness of the photoresist layer",
                    'B': "The wavelength of the exposure light",
                    'C': "The smallest feature size that can be reliably printed",
                    'D': "The size of the photomask"
                },
                'answer': 'C'
            },
            {
                'question': "Which process is used to remove unwanted material in semiconductor manufacturing?",
                'choices': {
                    'A': "Chemical Vapor Deposition (CVD)",
                    'B': "Physical Vapor Deposition (PVD)",
                    'C': "Ion Implantation",
                    'D': "Plasma Etching"
                },
                'answer': 'D'
            },
            {
                'question': "What is the primary function of EUV (Extreme Ultraviolet) lithography?",
                'choices': {
                    'A': "To enable patterning of sub-10nm features",
                    'B': "To reduce manufacturing costs",
                    'C': "To increase wafer throughput",
                    'D': "To eliminate the need for photomasks"
                },
                'answer': 'A'
            },
            {
                'question': "In memory technology, what distinguishes 3D NAND from 2D NAND?",
                'choices': {
                    'A': "Different programming voltages",
                    'B': "Vertical stacking of memory cells",
                    'C': "Use of different materials",
                    'D': "Different read/write speeds"
                },
                'answer': 'B'
            },
            {
                'question': "What is the main challenge in scaling below 7nm technology node?",
                'choices': {
                    'A': "Quantum tunneling effects",
                    'B': "Power consumption",
                    'C': "Manufacturing yield",
                    'D': "All of the above"
                },
                'answer': 'D'
            }
        ]
        
        q_data = random.choice(questions)
        return {
            'question': q_data['question'],
            'Answer': q_data['answer'],
            'A': q_data['choices']['A'],
            'B': q_data['choices']['B'], 
            'C': q_data['choices']['C'],
            'D': q_data['choices']['D'],
            'answer_type': 'multiple_choice'
        }

    def _generate_hle_question(self) -> Dict[str, Any]:
        """HLE (Humanity's Last Exam) 초고난이도 문제 생성"""
        # 60% 확률로 10지선다, 40% 확률로 주관식
        if random.random() < 0.6:
            # 10지선다 문제
            questions = [
                {
                    'question': "Consider the philosophical implications of Gödel's incompleteness theorems in the context of artificial intelligence. If we assume that human consciousness operates on principles that are fundamentally computational, what does this suggest about the ultimate limitations of artificial general intelligence in understanding itself?",
                    'choices': {
                        'A': "AGI will be forever limited by the same incompleteness that affects human reasoning",
                        'B': "AGI can transcend these limitations through meta-reasoning systems",
                        'C': "The question itself is malformed due to the category error of consciousness",
                        'D': "AGI will develop non-computational approaches to self-understanding",
                        'E': "Incompleteness theorems don't apply to consciousness-like processes",
                        'F': "AGI will create new logical frameworks beyond first-order logic",
                        'G': "The limitations are temporary and solvable through recursive self-improvement",
                        'H': "Human consciousness is not computational, making the premise invalid",
                        'I': "AGI will reach a state of perfect self-knowledge through quantum computation",
                        'J': "The answer depends on whether P=NP"
                    },
                    'answer': 'A'
                },
                {
                    'question': "In the context of multiverse theory and quantum mechanics, if every possible outcome of quantum events creates parallel universes, what are the ethical implications for decision-making in our observable universe?",
                    'choices': {
                        'A': "All moral decisions are meaningless since all outcomes occur somewhere",
                        'B': "We are only responsible for the measure of outcomes in our branch",
                        'C': "Ethics should maximize utility across all possible worlds",
                        'D': "Each decision creates moral responsibility in infinite universes",
                        'E': "Free will is an illusion, making ethics inapplicable",
                        'F': "We should act to minimize suffering in the highest-probability branches",
                        'G': "Moral frameworks must be reformulated for infinite outcome spaces",
                        'H': "The anthropic principle makes our choices uniquely significant",
                        'I': "Ethics collapses into aesthetic preferences across the multiverse",
                        'J': "We should optimize for the versions of ourselves we prefer to be"
                    },
                    'answer': 'G'
                },
                {
                    'question': "If consciousness is an emergent property of information integration (as suggested by Integrated Information Theory), and we can artificially create systems with arbitrary levels of information integration, what does this imply about the moral status of potential artificial consciousnesses?",
                    'choices': {
                        'A': "Artificial consciousness deserves rights proportional to its integration level",
                        'B': "Only naturally evolved consciousness has genuine moral status",
                        'C': "The substrate independence principle grants equal rights to all conscious entities",
                        'D': "Artificial consciousness might deserve greater moral consideration due to its designed nature",
                        'E': "Consciousness is not reducible to information integration",
                        'F': "We must develop new categories of rights for artificial minds",
                        'G': "The question presupposes consciousness can be objectively measured",
                        'H': "Moral status depends on the intentions behind consciousness creation",
                        'I': "Integration theory fails to capture the qualitative aspects of consciousness",
                        'J': "Different types of consciousness require different ethical frameworks"
                    },
                    'answer': 'F'
                }
            ]
            
            q_data = random.choice(questions)
            return {
                'question': q_data['question'],
                'Answer': q_data['answer'],
                'A': q_data['choices']['A'],
                'B': q_data['choices']['B'], 
                'C': q_data['choices']['C'],
                'D': q_data['choices']['D'],
                'E': q_data['choices']['E'],
                'F': q_data['choices']['F'],
                'G': q_data['choices']['G'],
                'H': q_data['choices']['H'],
                'I': q_data['choices']['I'],
                'J': q_data['choices']['J'],
                'answer_type': 'multiple_choice_10'
            }
        else:
            # 주관식 문제
            questions = [
                "Develop a comprehensive framework for evaluating the moral weight of potential suffering in artificial minds that might experience time non-linearly or have distributed consciousness across multiple substrates. Consider how traditional utilitarian calculus breaks down when dealing with entities that might experience thousands of subjective years in microseconds.",
                "Propose a solution to the alignment problem that addresses not just the goal-specification challenge, but also the fundamental epistemological question of how we can verify that an artificial superintelligence truly understands human values rather than simply optimizing for our observed behavioral patterns.",
                "Design a mathematical proof or disproof for whether consciousness can emerge from purely deterministic physical processes, while addressing the hard problem of consciousness and the explanatory gap between neural correlates and subjective experience.",
                "Construct an argument for or against the possibility that our universe is a simulation, considering the implications for physics, consciousness, and ethics. Address how we should behave if the simulation hypothesis is true and whether simulated beings have the same moral status as 'real' ones.",
                "Develop a novel ethical framework that can handle moral decisions involving entities with vastly different cognitive architectures, temporal experiences, and value systems - from biological humans to potential artificial minds to hypothetical alien intelligences.",
                "Analyze the paradox of self-improving artificial intelligence: if an AI system modifies itself to become more intelligent, at what point (if any) does it become a different entity with potentially different goals and values? What does this mean for continuity of identity and moral responsibility?"
            ]
            
            question = random.choice(questions)
            # 주관식 문제는 예시 답변을 제공
            sample_answers = [
                "A comprehensive analysis would need to address multiple dimensions of this complex problem...",
                "The solution requires a novel approach that integrates insights from philosophy, cognitive science, and mathematics...",
                "This proof would proceed by first establishing the necessary conditions for consciousness to emerge..."
            ]
            
            return {
                'question': question,
                'Answer': random.choice(sample_answers),
                'answer_type': 'open_ended'
            }

    def _generate_math_question(self) -> Dict[str, Any]:
        """수학 문제 생성"""
        questions = [
            "Solve the equation: 2x² - 5x + 3 = 0",
            "Find the integral of ∫(3x² + 2x - 1)dx",
            "Calculate the limit: lim(x→0) (sin(x)/x)",
            "Find the eigenvalues of the matrix [[2, 1], [1, 2]]",
            "Solve the differential equation: dy/dx = 2xy",
            "Find the Taylor series expansion of e^x around x = 0",
            "Calculate: ∫₀¹ x²e^x dx",
            "Find the inverse of the function f(x) = 3x + 7",
            "Determine if the series Σ(1/n²) converges or diverges",
            "Find the volume of the solid formed by rotating y = x² around the x-axis from x = 0 to x = 2"
        ]
        
        question = random.choice(questions)
        
        # 30% 확률로 객관식, 70% 확률로 숫자 답변
        if random.random() < 0.3:
            # 객관식
            answer = random.choice(['A', 'B', 'C', 'D'])
            choices = [
                f"x = {random.randint(1, 10)}", 
                f"x = {random.randint(1, 10)}", 
                f"No solution",
                f"x = {random.randint(1, 10)}"
            ]
            return {
                'question': question,
                'Answer': answer,
                'A': choices[0],
                'B': choices[1], 
                'C': choices[2],
                'D': choices[3],
                'answer_type': 'multiple_choice'
            }
        else:
            # 숫자 답변
            answer = random.randint(1, 100)
            return {
                'question': question,
                'Answer': str(answer),
                'answer_type': 'numeric'
            }

    def _generate_generic_question(self) -> Dict[str, Any]:
        """일반적인 질문 생성"""
        questions = [
            "What is the capital of France?",
            "Explain the concept of photosynthesis.",
            "Who painted the Mona Lisa?",
            "What is the largest planet in our solar system?",
            "Define artificial intelligence.",
            "What year did World War II end?",
            "Explain the water cycle.",
            "Who invented the telephone?",
            "What is the speed of light?",
            "Define democracy."
        ]
        
        return {
            'question': random.choice(questions),
            'Answer': random.choice(['A', 'B', 'C', 'D']),
            'answer_type': 'multiple_choice'
        }

    def generate_response(self, question: str, correct_answer: str, benchmark: str) -> str:
        """LLM 응답 생성"""
        if benchmark == 'aime':
            responses = [
                f"I need to solve this step by step.\n\nFirst, let me analyze the problem: {question}\n\nStep 1: Let me identify what we're looking for...\nStep 2: I'll use the appropriate mathematical technique...\nStep 3: Working through the calculations...\n\nTherefore, the answer is {correct_answer}.",
                f"Let me approach this systematically.\n\n{question}\n\nI'll break this down into manageable parts:\n- First, I need to understand the constraints\n- Then apply the relevant mathematical principles\n- Finally, compute the result\n\nAfter working through the problem, I get {correct_answer}.",
                f"This is a challenging problem that requires careful analysis.\n\n{question}\n\nLet me work through this:\n1. Set up the problem properly\n2. Apply the mathematical concepts\n3. Solve step by step\n\nThe final answer is {correct_answer}."
            ]
        elif benchmark == 'ds-mmlu':
            responses = [
                f"This is a semiconductor engineering question: {question}\n\nLet me analyze each option from a technical perspective:\n- Understanding the underlying physics and processes\n- Considering industry standards and best practices\n- Applying semiconductor device theory\n\nBased on my knowledge of semiconductor technology, the correct answer is {correct_answer}.",
                f"In semiconductor manufacturing: {question}\n\nThis requires knowledge of:\n- Process technology fundamentals\n- Device physics principles\n- Manufacturing considerations\n\nThe answer is {correct_answer}.",
                f"Analyzing this semiconductor question: {question}\n\nI need to consider the technical aspects and industry practices. The correct answer is {correct_answer}."
            ]
        elif benchmark == 'hle':
            if correct_answer in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
                # 10지선다
                responses = [
                    f"This is an extraordinarily complex philosophical question: {question}\n\nThis requires deep consideration of multiple philosophical frameworks, scientific theories, and logical implications. After careful analysis across various dimensions of this problem, I believe the most defensible position is {correct_answer}.",
                    f"Approaching this ultimate question: {question}\n\nThis intersects philosophy of mind, ethics, mathematics, and physics. The implications are profound and far-reaching. My analysis leads me to conclude that {correct_answer} represents the most coherent position.",
                    f"This question pushes the boundaries of human knowledge: {question}\n\nIntegrating insights from consciousness studies, mathematical logic, and moral philosophy, the answer appears to be {correct_answer}."
                ]
            else:
                # 주관식
                responses = [
                    f"This open-ended question requires a comprehensive framework: {question}\n\n{correct_answer}\n\nThis analysis integrates multiple philosophical and scientific perspectives to address the fundamental challenges presented.",
                    f"Addressing this profound question: {question}\n\n{correct_answer}\n\nThe framework developed here attempts to bridge theoretical insights with practical implications.",
                    f"This ultimate challenge requires novel thinking: {question}\n\n{correct_answer}\n\nThis approach synthesizes cutting-edge research across multiple domains."
                ]
        else:
            responses = [
                f"Looking at this question: {question}\n\nI need to consider each option carefully. Based on my knowledge, the correct answer is {correct_answer}.",
                f"To answer '{question}', I should analyze each possibility.\n\nAfter considering the options, I believe the answer is {correct_answer}.",
                f"This question asks: {question}\n\nLet me think through this systematically and arrive at the answer: {correct_answer}."
            ]
        
        return random.choice(responses)

    def generate_metadata(self, benchmark: str) -> Dict[str, Any]:
        """벤치마크별 메타데이터 생성"""
        base_metadata = {
            'id': random.randint(10000, 99999),
            'Difficulty': random.choice(self.difficulties),
            'business': random.choice(self.business_categories)  # 오타 유지
        }
        
        if benchmark == 'aime':
            base_metadata['competition_year'] = random.choice([2020, 2021, 2022, 2023, 2024])
            base_metadata['problem_number'] = random.randint(1, 15)
            # 특이한 메타데이터: 풀이에 필요한 단계 수
            base_metadata['solution_steps'] = random.randint(3, 12)
        
        if benchmark == 'mmlu':
            base_metadata['subject'] = random.choice(self.mmlu_subjects)
            base_metadata['category'] = random.choice(['STEM', 'Humanities', 'Social Science', 'Other'])
            # 특이한 메타데이터: 지식의 출처
            base_metadata['knowledge_source'] = random.choice([
                'Textbook', 'Wikipedia', 'Academic Paper', 'Encyclopedia', 'News Article', 
                'Government Document', 'Historical Record', 'Scientific Journal'
            ])
        
        if benchmark == 'mmlu-redux':
            base_metadata['subject'] = random.choice(self.mmlu_subjects)
            base_metadata['category'] = random.choice(['STEM', 'Humanities', 'Social Science', 'Other'])
            # 특이한 메타데이터: 문화적 맥락
            base_metadata['cultural_context'] = random.choice([
                'Korean', 'American', 'European', 'East Asian', 'Global', 'Western', 
                'Regional', 'Universal', 'Language-specific', 'Culture-neutral'
            ])
        
        if benchmark == 'mmlu-pro':
            base_metadata['subject'] = random.choice(self.mmlu_subjects)
            base_metadata['category'] = random.choice(['STEM', 'Humanities', 'Social Science', 'Other'])
            base_metadata['complexity'] = random.choice(['Basic', 'Intermediate', 'Advanced'])
            # 특이한 메타데이터: 학제간 연결성
            base_metadata['interdisciplinary'] = random.choice([
                'Single Domain', 'Cross-disciplinary', 'Multi-disciplinary', 'Transdisciplinary',
                'STEM-Humanities Bridge', 'Theory-Practice Bridge', 'Historical-Modern Bridge'
            ])
        
        if benchmark == 'math500':
            base_metadata['topic'] = random.choice(['Algebra', 'Calculus', 'Geometry', 'Statistics', 'Number Theory'])
            base_metadata['level'] = random.choice(['High School', 'Undergraduate', 'Graduate'])
            # 특이한 메타데이터: 증명 필요 여부
            base_metadata['proof_required'] = random.choice([True, False])
            base_metadata['theorem_dependency'] = random.choice([
                'Elementary', 'Intermediate Theorems', 'Advanced Theorems', 'Research Level',
                'Multiple Theorems', 'Novel Approach'
            ])
        
        if benchmark == 'ds-mmlu':
            base_metadata['subject'] = random.choice(self.dsmmlu_subjects)
            base_metadata['category'] = 'Semiconductor Engineering'
            base_metadata['Difficulty'] = random.choice(['Hard', 'Very Hard'])  # DS-MMLU는 전문적이므로 높은 난이도
            # 특이한 메타데이터: 산업 관련성
            base_metadata['industry_relevance'] = random.choice([
                'Fab Operations', 'Design Houses', 'Research Labs', 'Equipment Vendors',
                'Materials Suppliers', 'EDA Tools', 'Foundry Services', 'Test & Assembly',
                'Quality Control', 'Process Development'
            ])
        
        if benchmark == 'hle':
            base_metadata['category'] = random.choice(self.hle_categories)
            base_metadata['Difficulty'] = 'Extreme'  # HLE는 항상 최고 난이도
            base_metadata['complexity'] = 'Ultimate'
            base_metadata['philosophical_domain'] = random.choice([
                'Metaphysics', 'Epistemology', 'Ethics', 'Philosophy of Mind', 
                'Philosophy of Science', 'Applied Ethics', 'Logic'
            ])
            # 특이한 메타데이터: 학계 합의 수준
            base_metadata['consensus_level'] = random.choice([
                'Highly Contested', 'No Consensus', 'Emerging Consensus', 'Partial Agreement',
                'Active Debate', 'Paradigm Shift', 'Unresolved', 'Revolutionary',
                'Speculative', 'Frontier Research'
            ])
            # Dict 형식 메타데이터: 복잡도 세부 분석
            base_metadata['complexity_breakdown'] = {
                'mathematical_rigor': round(random.uniform(0.1, 1.0), 2),
                'philosophical_depth': round(random.uniform(0.5, 1.0), 2),
                'logical_complexity': round(random.uniform(0.3, 1.0), 2),
                'creativity_required': round(random.uniform(0.4, 1.0), 2),
                'interdisciplinary_scope': round(random.uniform(0.2, 1.0), 2),
                'abstract_reasoning': round(random.uniform(0.6, 1.0), 2),
                'novelty_factor': round(random.uniform(0.1, 0.9), 2),
                'ethical_implications': round(random.uniform(0.0, 1.0), 2)
            }
        
        return base_metadata

    def generate_item(self, benchmark: str, model: str) -> Dict[str, Any]:
        """단일 데이터 아이템 생성 (모델별 성능 차이 적용)"""
        # 기본 질문 데이터 생성
        q_data = self.generate_question_by_benchmark(benchmark)
        
        # 메타데이터 생성
        metadata = self.generate_metadata(benchmark)
        
        # LLM 응답 생성
        response = self.generate_response(q_data['question'], q_data['Answer'], benchmark)
        
        # 모델 성능 계산
        model_performance = self.get_model_performance(model, benchmark)
        
        # filtered_resps 생성 (모델 성능에 따른 답변)
        if q_data.get('answer_type') == 'numeric':
            try:
                base_answer = int(q_data['Answer'])
                # 모델 성능에 따라 오차 범위 결정
                if random.random() < model_performance:
                    # 정답 또는 근사값
                    max_error = max(1, int((1 - model_performance) * 10))
                    filtered_resps = base_answer + random.randint(-max_error, max_error)
                else:
                    # 완전히 틀린 답
                    filtered_resps = base_answer + random.randint(-50, 50)
            except (ValueError, TypeError):
                filtered_resps = q_data['Answer'] if random.random() < model_performance else "Unknown"
                
        elif q_data.get('answer_type') == 'open_ended':
            # 주관식 문제는 모델 성능에 따라 답변 품질 조정
            if random.random() < model_performance:
                filtered_resps = q_data['Answer']
            else:
                # 성능이 낮으면 더 간단하거나 부정확한 답변
                simple_answers = [
                    "This is a complex topic that requires further research.",
                    "I need more information to provide a complete answer.",
                    "This question involves multiple philosophical considerations."
                ]
                filtered_resps = random.choice(simple_answers)
                
        else:
            # 객관식 (4지선다 또는 10지선다)
            if random.random() < model_performance:
                # 정답
                filtered_resps = q_data['Answer']
            else:
                # 오답 선택
                if q_data.get('answer_type') == 'multiple_choice_10':
                    choices = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
                else:
                    choices = ['A', 'B', 'C', 'D']
                
                if q_data['Answer'] in choices:
                    choices.remove(q_data['Answer'])
                filtered_resps = random.choice(choices)
        
        # match 계산 (모델 성능 기반)
        if q_data.get('answer_type') == 'open_ended':
            # 주관식은 모델 성능 기반 점수
            if filtered_resps == q_data['Answer']:
                match = model_performance
            else:
                match = model_performance * random.uniform(0.3, 0.7)
                
        elif str(filtered_resps).strip() == str(q_data['Answer']).strip():
            match = 1.0
            
        else:
            # 부분 점수 (수학 문제의 경우)
            if benchmark in ['aime', 'math500'] and q_data.get('answer_type') == 'numeric':
                try:
                    correct = float(q_data['Answer'])
                    predicted = float(filtered_resps)
                    diff = abs(correct - predicted)
                    if diff == 0:
                        match = 1.0
                    elif diff <= 2:
                        match = 0.5 * model_performance
                    elif diff <= 5:
                        match = 0.2 * model_performance
                    else:
                        match = 0.0
                except (ValueError, TypeError):
                    match = 0.0
            else:
                match = 0.0
        
        # 최종 데이터 조합
        item = metadata.copy()
        item.update({
            'question': q_data['question'],
            'Answer': q_data['Answer'],
            'response': response,
            'filtered_resps': filtered_resps,
            'match': match
        })
        
        # 객관식의 경우 선택지 추가
        if 'A' in q_data:
            item['A'] = q_data['A']
            item['B'] = q_data['B']
            item['C'] = q_data['C']
            item['D'] = q_data['D']
            
        # 10지선다의 경우 추가 선택지
        if q_data.get('answer_type') == 'multiple_choice_10':
            item['E'] = q_data['E']
            item['F'] = q_data['F']
            item['G'] = q_data['G']
            item['H'] = q_data['H']
            item['I'] = q_data['I']
            item['J'] = q_data['J']
        
        return item

    def generate_dataset(self, benchmark: str, model: str, size: int = 100) -> List[Dict[str, Any]]:
        """전체 데이터셋 생성 (모델별)"""
        return [self.generate_item(benchmark, model) for _ in range(size)]

    def save_datasets(self, output_dir: str = './our_results', items_per_file: int = 500):
        """모든 데이터셋 파일 생성 및 저장"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"데이터셋 생성을 시작합니다...")
        print(f"모델 수: {len(self.models)}")
        print(f"벤치마크 수: {len(self.benchmarks)}")
        print(f"파일당 아이템 수: {items_per_file}")
        print(f"새로 추가된 벤치마크: ds-mmlu (반도체), HLE (Humanity's Last Exam)")
        print(f"모델별 성능 차이가 크게 적용됩니다.")
        
        total_files = 0
        
        for model in self.models:
            model_dir = os.path.join(output_dir, model)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            
            for benchmark in self.benchmarks:
                print(f"생성 중: {model}/{benchmark}.json (성능: {self.get_model_performance(model, benchmark):.2f})")
                
                # 데이터셋 생성 (모델별 성능 적용)
                dataset = self.generate_dataset(benchmark, model, items_per_file)
                
                # 파일 저장
                filepath = os.path.join(model_dir, f"{benchmark}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
                
                total_files += 1
                avg_score = sum(item['match'] for item in dataset) / len(dataset)
                print(f"✓ 저장 완료: {filepath} ({len(dataset)} items, 평균 점수: {avg_score:.3f})")
        
        print(f"\n총 {total_files}개 파일이 생성되었습니다.")
        print(f"총 데이터 아이템 수: {total_files * items_per_file:,}개")
        
        # 모델별 성능 요약 출력
        print(f"\n=== 모델별 성능 요약 ===")
        for model in self.models:
            performances = []
            for benchmark in self.benchmarks:
                perf = self.get_model_performance(model, benchmark)
                performances.append(perf)
            avg_perf = sum(performances) / len(performances)
            print(f"{model}: 평균 {avg_perf:.3f} (범위: {min(performances):.3f}-{max(performances):.3f})")
            
        return total_files

# 사용 예시
if __name__ == "__main__":
    generator = FakeDatasetGenerator()
    
    # 데이터셋 생성 (각 파일당 500개 아이템)
    generator.save_datasets(items_per_file=5500)
    
    # 새로 추가된 벤치마크 테스트
    print("\n=== DS-MMLU 샘플 ===")
    dsmmlu_sample = generator.generate_item('ds-mmlu', 'deepseek-r1')
    print(json.dumps(dsmmlu_sample, ensure_ascii=False, indent=2))
    
    print("\n=== HLE 샘플 (10지선다) ===")
    hle_sample = generator.generate_item('hle', 'gpt-4o')
    print(json.dumps(hle_sample, ensure_ascii=False, indent=2))