# DukaanAI: AI & Language Architecture

## 1. High-Level AI Strategy

DukaanAI employs a **Hybrid Edge-Cloud Architecture** designed for high latency resilience, cost efficiency, and zero tolerance for calculation hallucinations.

```
+---------------------------------------------------------------------------------+
|                                 1. Client Edge                                  |
|                                                                                 |
|  [Merchant Voice] -> Audio Record -> On-device VAD (Voice Activity Detection)    |
|                                   -> Lightweight ASR / Cloud ASR Audio Stream    |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                               2. AI Gateway Plane                               |
|                                                                                 |
|  Audio / Hinglish Transcript -> Phonetic Normalizer & Tokenizer                 |
|                              -> Intent Classifier (POS, KHATA, EXPENSE, QUERY)  |
|                              -> LLM Slot & Entity Extractor                     |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                      3. Strict Schema & Tool Validation                         |
|                                                                                 |
|  LLM generates Structured Draft:                                                |
|  { "intent": "ADD_CUSTOMER_CREDIT", "customer": "Ramesh", "amount": 250.00 }   |
|  (Pydantic Schema Validation -> Catalog & Customer Disambiguation)              |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                    4. Deterministic Business Execution                          |
|                                                                                 |
|  - Validated Draft is returned to Client UI as a Confirmation Card              |
|  - Shopkeeper taps "Confirm" (or cancels)                                       |
|  - Deterministic Ledger Engine commits to Room & PostgreSQL                     |
+---------------------------------------------------------------------------------+
```

---

## 2. Core AI Principles

### 2.1 Principle 1: Zero Computational Trust in LLMs
- **LLMs are language interpreters, not calculators**.
- An LLM must **never** calculate item subtotals, tax brackets, discounts, or balance totals.
- The LLM extracts tokens: `[item="Atta", quantity=5, unit="kg", price_per_unit=42]`.
- The deterministic calculation engine computes: `5 * 42 = 210`.

### 2.2 Principle 2: Human-In-The-Loop Confirmation
- Voice-driven actions never commit blindly to the financial ledger.
- Extracted transactions produce a high-contrast, large-button confirmation card on the screen.
- 1-tap confirmation guarantees shopkeeper control and audits mistakes before persistence.

### 2.3 Principle 3: Provider-Agnostic LLM Abstraction
- All AI model interactions implement a unified Python interface:
  ```python
  class BaseLanguageModel(ABC):
      @abstractmethod
      async def generate_structured(
          self,
          prompt: str,
          response_schema: type[T],
          system_prompt: str | None = None
      ) -> T:
          ...
  ```
- Concrete adapters are implemented for Anthropic, OpenAI, Google Gemini, and local small language models (SLMs) such as Mistral or Llama on-premise.

---

## 3. Hinglish Language Processing

Retail conversations in Indian shops feature dynamic code-switching:
- Example: *"Shyam Lal ji ne teen packet Maggi aur do kilo chawal liya, unke khate me likho."*
- Example: *"Aata ka stock kitna hai check karo."*

### Pipeline:
1. **Audio Ingestion**: Opus-compressed audio stream uploaded to backend.
2. **ASR (Speech-to-Text)**: Whisper or Indic-ASR tuned for Hindi-English phonetic transcription.
3. **Phonetic & Dialect Normalization**: Canonicalizes variations (e.g., *kg*, *kilo*, *keji*; *aata*, *atta*; *khata*, *khaata*).
4. **Disambiguation Engine**: Matches fuzzy names against the merchant's local customer list and product catalog (e.g., *"Maggi"* matched to SKU `MAGGI-70G-IN`).
5. **Slot Extraction**: Populates strongly-typed Pydantic draft models.

---

## 4. Evaluative Benchmarks & Safety

The `ml/evaluation` suite tracks:
- **Slot Extraction Accuracy**: Precision/Recall on quantities, units, and customer entities.
- **Intent Misclassification Rate**: Guarding against recording an inquiry as a financial transaction.
- **Inference Latency Target**: P95 < 1200ms end-to-end (voice audio to UI confirmation card).
