import ast
import datetime
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def functions(relative, names, **context):
    source=ast.parse((ROOT/relative).read_text(encoding="utf-8"))
    nodes=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0)]
    nodes.extend(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names)
    namespace={"pd":pd,"datetime":datetime,"sys":sys,**context}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),relative,"exec"),namespace)
    return namespace

class MigrationTests(unittest.TestCase):
    def test_constituent_query_uses_supported_stock_pool(self):
        sdk=Mock()
        def details(fields=None,status=None):
            return pd.DataFrame([{"symbol":"000001.SZ","listed_date":"19910403"}])
        def factor(symbol,start_date,end_date,factors,type="stock",index_component=None):
            self.assertEqual(type,"stock")
            if not symbol:self.assertEqual(index_component,"000300")
            return pd.DataFrame([{"symbol":"000001.SZ","date":"20250115","market_cap":100,"close":10,"turnover":1}])
        sdk.get_stock_detail.side_effect=details;sdk.get_factor.side_effect=factor
        sdk.get_fina_performance.return_value=pd.DataFrame([{"symbol":"000001.SZ"}])
        ns=functions("examples/ep_factor_analysis.py",{"fetch_data"},FACTOR_DATE="20250115",QUARTER="2024q4",_filter_new_stocks=lambda symbols,detail:symbols)
        with patch.dict(sys.modules,{"panda_data":sdk}):
            data,symbols=ns["fetch_data"]()
        self.assertEqual(symbols,["000001.SZ"])
        self.assertEqual(len(data),1)

if __name__=="__main__":unittest.main()
