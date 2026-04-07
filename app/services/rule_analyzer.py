'''
это код второго слоя проверки дедубликации. В первом слое были выбраны канидаты с наиболее большей вероятностью дубликации. Здесь эти кандидаты будут проверяться с помощью правил с товаров пользователя, здесь же будет производиться заключение является ли товар пользователя дубликатом или нет.
'''
'''
This is the code for the second deduplication ckeck layer. In the first layer were chosen candidates with the highest possibility of duplication. These candidates will be checked here with help of custom user's rules, here also will be decided is new produtc duplicate or not.
'''


import re 
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
import yaml


@dataclass
class DuplicateRules:
    'Duplication rules container'
    brand_normalization: Dict[str, str] = field(default_factory=dict)
    modifiers: List[str] = field(default_factory=list)
    category_keywords: Dict[str, List[str]] = field(default_factory=dict)
    custom_checkers: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def load_from_yaml(cls, path: str) -> 'DuplicateRules':
        "Downloading rules from .yaml file"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

                return cls(
                    brand_normalization=data.get('brand_normalization', {}),
                    modifiers=data.get('modifiers', []),
                    category_keywords=data.get('category_keywords', {}),
                    custom_checkers=data.get('custom_checkers', [])
                )
        
        except FileNotFoundError:
                print(f"⚠️ Rules file not found. Using default rules.")
                return cls()
        except yaml.YAMLError as e:
            print(f"❌ Parsing error YAML: {e}")
            return cls()
    
    @classmethod
    def create_default(cls) -> 'DuplicateRules':
        """Creating default rules"""
        return cls(
            brand_normalization={
                # Sony
                'ps': 'sony',
                'playstation': 'sony',
                'ps5': 'sony',
                'ps4': 'sony',
                
                # NVIDIA
                'rtx': 'nvidia',
                'gtx': 'nvidia',
                'nvidia': 'nvidia',
                
                # Apple
                'iphone': 'apple',
                'ipad': 'apple',
                'macbook': 'apple',
                'apple': 'apple',
                
                # Samsung
                'samsung': 'samsung',
                'galaxy': 'samsung',
                
                # Microsoft
                'xbox': 'microsoft',
            },
            modifiers=[
                'ti', 'pro', 'max', 'ultra', 'plus', 
                'lite', 'se', 'air', 'mini'
            ],
            category_keywords={
                'gpu': ['rtx', 'gtx', 'graphics', 'видеокарта'],
                'smartphone': ['iphone', 'galaxy', 'smartphone', 'смартфон'],
                'console': ['playstation', 'ps', 'xbox', 'nintendo', 'консоль'],
                'laptop': ['macbook', 'thinkpad', 'laptop', 'ноутбук'],
            }
        )

    def reset_to_default_rules(self):
        """Reset rules to default"""
        return DuplicateRules.create_default()


class DuplicateAnalyzer:
    """
    Second layer of verification: structual analysis
    """

    def __init__(self, rules: Optional[DuplicateRules] = None):
        """
        Analysator initialization
        
        Args:
            rules: Deduplication rules. If not defined - using default 
        """

        self.rules = rules or DuplicateRules.create_default()

        self.number_pattern = re.compile(r'\b\d{3,4}\b')
        
    def update_rules(self, rules: DuplicateRules):
        self.rules = rules
    

# ------------------------ Extraction methods ---------------------------

    def extract_number(self, text:str) -> List[str]:
        '''
        extracting numbers from products
        '''
        numbers = re.findall(r'\b\d{3,4}\b', text)
        return numbers
    
    def extract_modifiers(self, text:str) -> List[str]:
        '''
        extracting modifiers from products
        '''
        text_lower = text.lower()
        found_modifiers = []

        for modifier in self.rules.modifiers:
            if re.search(rf'\b{modifier}\b', text_lower):
                found_modifiers.append(modifier)

        return found_modifiers

    def extract_brand(self, text:str) -> Optional[str]:
        '''
        extracting brands from products
        '''
        text_lower = text.lower()

        for keyword, brand in self.rules.brand_normalization.items():
            if keyword in text_lower:
                return brand
        
        return None
    
    def extract_category(self, text:str) -> Optional[str]:
        ''''
        extracting categories from products
        '''
        text_lower = text.lower()

        for category, keywords in self.rules.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return None
    
#------------------------ Comparement section ---------------------------

    def compare_numbers(self, text1: str, text2: str) -> Tuple[bool, str]:
        '''
        number codes comparison
        returns tuple, that includes bool and the reason (for tests)
        '''

        number1 = self.extract_number(text1)
        number2 = self.extract_number(text2)

        if not number1 or not number2:
            return False, "no_numbers"
        
        if set(number1) != set(number2):
            return True, f"different_numbers: {number1, number2}"
        
        return False, f"duplicate: {number1, number2}"

    def compare_modifiers(self, text1: str, text2: str) -> Tuple[bool, str]:
        '''
        modifiers comparison
        '''
        modifier1 = set(self.extract_modifiers(text1))
        modifier2 = set(self.extract_modifiers(text2))

        if not modifier1 and not modifier2:
            return False, "no_modifiers"
        
        if modifier1 != modifier2:
            return True, f"different_modifiers: {modifier1, modifier2}"

        return False, f"same_modifiers ({modifier1})"
    
    def compare_brands(self, text1: str, text2: str) -> Tuple[bool, str]:
        '''
        brands comparison
        '''

        brand1 = self.extract_brand(text1)
        brand2 = self.extract_brand(text2)

        if not brand1 or not brand2:
            return False, 'unknown brand'
        
        if brand1 != brand2:
            return True, f'different_brands: {brand1, brand2}'
        
        return False, f'same_brand{brand1}'
    
    def compare_categories(self, text1: str, text2: str) -> Tuple[bool, str]:
        '''
        categories comparison
        '''

        category1 = self.extract_category(text1)
        category2 = self.extract_category(text2)

        if not category1 or not category2:
            return False, "unknown_category"
        
        if category1 != category2:
            return True, f'different_categories: {category1, category2}'
        
        return False, f'same_category: {category1}'
    

#------------------------ Analyzing section ---------------------------
    def Analyze(self, text1: str, text2: str) -> Dict[str, Any]:
        '''
        final decision function
        returns the result in bool and the list of reasons (for tests)
        '''

        reasons = []

        #numbers check
        numbers_diff, numbers_reason = self.compare_numbers(text1, text2)
        reasons.append(f'Numbers: {numbers_reason}')

        if numbers_diff:
            return {
                'state':False, 
                'reasons':reasons
            }
                
        #modifiers check
        modifiers_diff, modifiers_reason = self.compare_modifiers(text1, text2)
        reasons.append(f'Modifiers: {modifiers_reason}')

        if modifiers_diff:
            return {
                'state':False, 
                'reasons':reasons
            }
        
        #brands check
        brands_diff, brands_reason = self.compare_brands(text1, text2)
        reasons.append(f'Brands: {brands_reason}')

        if brands_diff:
            return {
                'state':False, 
                'reasons':reasons
            }
        
        #categories check
        category_diff, category_reason = self.compare_categories(text1, text2)
        reasons.append(f'Categories: {category_reason}')

        if category_diff:
            return {
                'state':False, 
                'reasons':reasons
            }
        
        return {
                'state':True, 
                'reasons':reasons
            }
    





