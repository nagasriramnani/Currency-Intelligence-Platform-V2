# Local Editor Agent - TinyLlama Integration
import logging
import threading
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LocalEditorAgent:
    _instance = None
    _lock = threading.Lock()
    _pipe = None
    _tokenizer = None
    _initialized = False
    MODEL_ID = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
    MAX_NEW_TOKENS = 100
    TEMPERATURE = 0.7
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def _ensure_loaded(self):
        if self._initialized:
            return True
        with self._lock:
            if self._initialized:
                return True
            try:
                logger.info('Loading LLM: ' + self.MODEL_ID)
                import torch
                from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
                kwargs = {'trust_remote_code': True}
                if device == 'cpu':
                    kwargs['torch_dtype'] = torch.float32
                model = AutoModelForCausalLM.from_pretrained(self.MODEL_ID, **kwargs)
                if device == 'cpu':
                    model = model.to('cpu')
                self._pipe = pipeline('text-generation', model=model, tokenizer=self._tokenizer, device=0 if device == 'cuda' else -1)
                self._initialized = True
                return True
            except Exception as e:
                logger.error('Failed to load LLM: ' + str(e))
                return False
    
    def generate_summary(self, company_name, raw_news, max_sentences=2):
        result = {'company_name': company_name, 'summary': None, 'success': False, 'fallback_used': False}
        if not raw_news or len(raw_news.strip()) < 50:
            result['summary'] = 'No recent news available for ' + company_name + '.'
            result['success'] = True
            result['fallback_used'] = True
            return result
        if not self._ensure_loaded():
            result['summary'] = self._fallback_summary(company_name, raw_news)
            result['success'] = True
            result['fallback_used'] = True
            return result
        try:
            prompt = self._build_prompt(company_name, raw_news, max_sentences)
            outputs = self._pipe(prompt, max_new_tokens=self.MAX_NEW_TOKENS, temperature=self.TEMPERATURE, do_sample=True, top_p=0.9, pad_token_id=self._tokenizer.eos_token_id)
            summary = outputs[0]['generated_text'][len(prompt):].strip()
            summary = self._clean_summary(summary, max_sentences)
            result['summary'] = summary
            result['success'] = True
        except Exception as e:
            result['summary'] = self._fallback_summary(company_name, raw_news)
            result['success'] = True
            result['fallback_used'] = True
        return result
    
    def _build_prompt(self, company_name, raw_news, max_sentences):
        if len(raw_news) > 1500:
            raw_news = raw_news[:1500] + '...'
        system_msg = 'You are an investment analyst. Write exactly ' + str(max_sentences) + ' sentences summarizing key business developments. Be factual.'
        user_msg = 'Company: ' + company_name + '. News: ' + raw_news + '. Summary:'
        EOS = chr(60) + '/s' + chr(62)
        SYS_START = chr(60) + '|system|' + chr(62)
        USR_START = chr(60) + '|user|' + chr(62)
        prompt = SYS_START + system_msg + EOS + USR_START + user_msg + EOS
        return prompt
    
    def _clean_summary(self, text, max_sentences):
        if not text:
            return ''
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > max_sentences:
            sentences = sentences[:max_sentences]
        return ' '.join(sentences)
    
    def _fallback_summary(self, company_name, raw_news):
        first_100 = raw_news[:200].strip() if raw_news else ''
        if first_100:
            return company_name + ' in the news. ' + first_100 + '...'
        return 'No summary available for ' + company_name + '.'
