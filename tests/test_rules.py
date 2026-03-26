"""
test_rules.py
Regression tests for all rules.
Run with: pytest tests/test_rules.py -v
Or:        python tests/test_rules.py
"""
from __future__ import annotations
import sys
from pathlib import Path
# Support running from project root or tests/ directory
_src = Path(__file__).parent.parent / "src"
if _src.exists():
    sys.path.insert(0, str(_src))
sys.path.insert(0, str(Path(__file__).parent))

from rules_i import (
    apply_i1, apply_i2, apply_i3, apply_i4, apply_i5,
    apply_i6, apply_i7, apply_i8, apply_i9, apply_i10,
    apply_all_i_rules,
)
from rules_b import apply_all_b_rules
from dedup import deduplicate


# ===========================================================================
# I-1: Suffix placement
# ===========================================================================
class TestI1:
    def test_comma_before_jr_removed(self):
        assert apply_i1("CHAMBERS, GARY MADOX, JR") == "CHAMBERS, GARY MADOX JR"

    def test_comma_before_sr_removed(self):
        assert apply_i1("JONES, BILL, SR") == "JONES, BILL SR"

    def test_no_comma_before_jr_unchanged(self):
        assert apply_i1("CHAMBERS, GARY MADOX JR") == "CHAMBERS, GARY MADOX JR"

    def test_no_suffix_unchanged(self):
        assert apply_i1("SMITH, JOHN") == "SMITH, JOHN"

    def test_roman_numeral_suffix(self):
        assert apply_i1("KING, JAMES, III") == "KING, JAMES III"


# ===========================================================================
# I-2: Delete junk rows
# ===========================================================================
class TestI2:
    def test_just_comma(self):
        assert apply_i2(",") is None

    def test_comma_space(self):
        assert apply_i2(", ") is None

    def test_movant(self):
        assert apply_i2("MOVANT, ") is None

    def test_lienholder_alone(self):
        assert apply_i2("LIENHOLDER,") is None

    def test_real_name_kept(self):
        assert apply_i2("SMITH, JOHN") == "SMITH, JOHN"

    def test_empty_string(self):
        assert apply_i2("") is None


# ===========================================================================
# I-3: Strip legal fragments
# ===========================================================================
class TestI3:
    def test_in_rem_only(self):
        assert apply_i3("SMITH, IN REM ONLY HARRY") == "SMITH, HARRY"

    def test_lienholder_in_rem_only(self):
        assert apply_i3("RAY, LIENHOLDER IN REM ONLY JOE DEE") == "RAY, JOE DEE"

    def test_trustee(self):
        assert apply_i3("HOOGENDOORN, LARRY TRUSTEE W") == "HOOGENDOORN, LARRY W"

    def test_in_rem(self):
        assert apply_i3("NEALE, IN REM JIM") == "NEALE, JIM"

    def test_individually(self):
        assert apply_i3("WHITE, MICHELLE MARIE INDIVIDUALLY") == "WHITE, MICHELLE MARIE"

    def test_no_fragment_unchanged(self):
        assert apply_i3("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# I-4: Inverted names
# ===========================================================================
class TestI4:
    def test_single_word_after_comma(self):
        assert apply_i4("CHERYL, WOODALL") == "WOODALL, CHERYL"

    def test_apellido_initial(self):
        assert apply_i4("JOHN, STOVER A") == "STOVER, JOHN A"

    def test_middle_then_apellido(self):
        assert apply_i4("JIMMY, LEE EARLY") == "EARLY, JIMMY LEE"

    def test_two_words_after_comma(self):
        assert apply_i4("JOHN, DAVID BARNES") == "BARNES, JOHN DAVID"

    def test_unknown_first_name_unchanged(self):
        assert apply_i4("SMITH, JOHN") == "SMITH, JOHN"

    def test_mary_inverted(self):
        assert apply_i4("MARY, JONES") == "JONES, MARY"


# ===========================================================================
# I-5: THE, OR pattern
# ===========================================================================
class TestI5:
    def test_with_initial(self):
        assert apply_i5("THE, OR DALE GOUGE R") == "GOUGE, DALE R"

    def test_two_words_no_initial(self):
        assert apply_i5("THE, OR NANNETT SHIREY") == "SHIREY, NANNETT"

    def test_three_words_no_initial(self):
        assert apply_i5("THE, OR TROY EDWARD MARDIS") == "MARDIS, TROY EDWARD"

    def test_with_initial_long(self):
        assert apply_i5("THE, OR DELBERT NEJMANOWSKI D") == "NEJMANOWSKI, DELBERT D"

    def test_ouida_jackson(self):
        assert apply_i5("THE, OR OUIDA JACKSON W") == "JACKSON, OUIDA W"

    def test_no_match_unchanged(self):
        assert apply_i5("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# I-6: THE-APELLIDO, OR pattern
# ===========================================================================
class TestI6:
    def test_two_initials(self):
        assert apply_i6("THE-ROBERTS, OR JA") == "ROBERTS, JA"

    def test_two_initials_variant(self):
        assert apply_i6("THE-ROBERTS, OR KJ") == "ROBERTS, KJ"

    def test_no_match_unchanged(self):
        assert apply_i6("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# I-7: FOR, pattern
# ===========================================================================
class TestI7:
    def test_with_initial(self):
        assert apply_i7("FOR, ELZIE TAYLOR A") == "TAYLOR, ELZIE A"

    def test_no_match_unchanged(self):
        assert apply_i7("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# I-8: THE ESTATE OF
# ===========================================================================
class TestI8:
    def test_estate_of_with_jr(self):
        assert apply_i8("THE ESTATE OF JIMMY LEE EARLY JR") == "EARLY, JIMMY LEE JR"

    def test_estate_typo(self):
        assert apply_i8("THE ESTAET OF JIMMY LEE EARLY JR") == "EARLY, JIMMY LEE JR"

    def test_estate_no_suffix(self):
        assert apply_i8("THE ESTATE OF MARY JANE SMITH") == "SMITH, MARY JANE"

    def test_no_match_unchanged(self):
        assert apply_i8("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# I-9: THE UNKNOWN HEIRS
# ===========================================================================
class TestI9:
    def test_full_pattern(self):
        result, _ = apply_all_i_rules(
            "THE UNKNOWN HEIRS OR DEVISEES OF THE ESTATE OF JIMMY LEE EARLY, DECEASED"
        )
        assert result == "EARLY, JIMMY LEE"


# ===========================================================================
# I-10: No comma fallback
# ===========================================================================
class TestI10:
    def test_two_tokens(self):
        assert apply_i10("WRIGHT JENNIFER") == "WRIGHT, JENNIFER"

    def test_three_tokens(self):
        assert apply_i10("SMITH JOHN R") == "SMITH, JOHN R"

    def test_has_comma_unchanged(self):
        assert apply_i10("SMITH, JOHN") == "SMITH, JOHN"


# ===========================================================================
# apply_all_i_rules: integration
# ===========================================================================
class TestApplyAllIRules:
    def test_normal_name_unchanged(self):
        result, rule = apply_all_i_rules("CORNWELL, LORENE")
        assert result == "CORNWELL, LORENE"

    def test_i2_delete(self):
        result, rule = apply_all_i_rules(",")
        assert result is None
        assert rule == "I-2"

    def test_i3_then_i1(self):
        result, rule = apply_all_i_rules("SMITH, IN REM ONLY HARRY, JR")
        assert result == "SMITH, HARRY JR"

    def test_i8_before_i3(self):
        result, rule = apply_all_i_rules("THE ESTATE OF JIMMY LEE EARLY JR")
        assert result == "EARLY, JIMMY LEE JR"
        assert rule == "I-8"

    def test_i6_before_i5(self):
        result, rule = apply_all_i_rules("THE-ROBERTS, OR JA")
        assert result == "ROBERTS, JA"
        assert rule == "I-6"


# ===========================================================================
# B rules
# ===========================================================================
class TestBRules:
    def test_b2_isd(self):
        result, rule = apply_all_b_rules("ISD POTTSBORO")
        assert result == "POTTSBORO ISD"
        assert rule == "B-2"

    def test_b2_hospital(self):
        result, rule = apply_all_b_rules("HOSPITAL WILSON N JONES MEMORIAL")
        assert result == "WILSON N JONES MEMORIAL HOSPITAL"

    def test_b2_bank(self):
        result, rule = apply_all_b_rules("BANK GRAYSON COUNTY STATE")
        assert result == "GRAYSON COUNTY STATE BANK"

    def test_b2_na_prefix(self):
        result, rule = apply_all_b_rules("NA CITIBANK SOUTH DAKOTA")
        assert result == "CITIBANK SOUTH DAKOTA NA"

    def test_b2_authority(self):
        result, rule = apply_all_b_rules("AUTHORITY DENISON HOSPITAL")
        assert result == "DENISON HOSPITAL AUTHORITY"

    def test_b2_jail(self):
        result, rule = apply_all_b_rules("JAIL GRAYSON COUNTY")
        assert result == "GRAYSON COUNTY JAIL"

    def test_b2_estate(self):
        result, rule = apply_all_b_rules("ESTATE JIM HARROD REAL")
        assert result == "JIM HARROD REAL ESTATE"

    def test_b3_state_of(self):
        result, rule = apply_all_b_rules("TEXAS STATE OF")
        assert result == "STATE OF TEXAS"
        assert rule == "B-3"

    def test_b3_county_of(self):
        result, rule = apply_all_b_rules("GRAYSON COUNTY OF")
        assert result == "GRAYSON COUNTY"
        assert rule == "B-3"

    def test_b4_two_businesses(self):
        result, rule = apply_all_b_rules("CORP COMMTRON CORPORATION AND EMERSON RADIO")
        assert isinstance(result, list)
        assert rule == "B-4"
        assert len(result) == 2
        assert all(r["marker"] == "B" for r in result)

    def test_b5_wife_pattern(self):
        result, rule = apply_all_b_rules("MILLS JAMES E AND WIFE LINDA D MILLS")
        assert isinstance(result, list)
        assert rule == "B-5"
        assert result[0] == {"marker": "I", "name": "MILLS, JAMES E"}
        assert result[1] == {"marker": "I", "name": "MILLS, LINDA D"}

    def test_b5_shared_surname(self):
        result, rule = apply_all_b_rules("STRAIN DONALD AND DOROTHY STRAIN")
        assert isinstance(result, list)
        assert result[0] == {"marker": "I", "name": "STRAIN, DONALD"}
        assert result[1] == {"marker": "I", "name": "STRAIN, DOROTHY"}

    def test_b1_sears_not_split(self):
        result, rule = apply_all_b_rules("SEARS ROEBUCK AND CO")
        assert result == "SEARS ROEBUCK AND CO"
        assert rule == "B-1"

    def test_b1_inc_unchanged(self):
        result, rule = apply_all_b_rules("MIT-CON INC")
        assert result == "MIT-CON INC"
        assert rule == "B-1"

    def test_b5_young_marsha_and_david(self):
        """Single surname shared — DAVID inherits YOUNG"""
        result, rule = apply_all_b_rules("YOUNG MARSHA AND DAVID")
        assert rule == "B-5"
        assert result == [{"marker": "I", "name": "YOUNG, MARSHA"},
                          {"marker": "I", "name": "YOUNG, DAVID"}]

    def test_b1_service_b_and_b_sales(self):
        """SERVICE record with single-letter tokens — do not split"""
        result, rule = apply_all_b_rules("SERVICE B AND B SALES AND")
        assert rule == "B-1"
        assert result == "SERVICE B AND B SALES AND"

    def test_b5_densmore_in_the(self):
        """Strip IN THE, split with shared surname DENSMORE"""
        result, rule = apply_all_b_rules("DENSMORE SHAWN WESTLY AND CHRISTY LYNN IN THE")
        assert rule == "B-5"
        assert result == [{"marker": "I", "name": "DENSMORE, SHAWN WESTLY"},
                          {"marker": "I", "name": "DENSMORE, CHRISTY LYNN"}]

    def test_b2_company_before_and_split(self):
        """Descriptive prefix COMPANY moves to end — no AND split"""
        result, rule = apply_all_b_rules("COMPANY TRADERS AND GENERAL INSURANCE")
        assert rule == "B-2"
        assert result == "TRADERS AND GENERAL INSURANCE COMPANY"

    def test_b8_person_with_number(self):
        result, rule = apply_all_b_rules("VANVORST MICHAEL J 8207424")
        assert isinstance(result, dict)
        assert result["marker"] == "I"
        assert result["name"] == "VANVORST, MICHAEL J"
        assert rule == "B-8"


# ===========================================================================
# Deduplication
# ===========================================================================
class TestDedup:
    class FakeLine:
        def __init__(self, marker, name):
            self.marker = marker
            self.name = name
            self.raw = f"\t\t\t\t{marker}\t{name}\n"
            self.line_number = 0

        @property
        def needs_processing(self):
            return self.marker in ("I", "B")

        @property
        def is_short(self):
            return False

    def test_exact_duplicate_removed(self):
        lines = [self.FakeLine("I", "SMITH, JOHN"), self.FakeLine("I", "SMITH, JOHN")]
        result, removed = deduplicate(lines)
        assert len(result) == 1
        assert removed == 1

    def test_jr_exception_both_kept(self):
        lines = [
            self.FakeLine("I", "EARLY, JIMMY LEE JR"),
            self.FakeLine("I", "EARLY, JIMMY LEE"),
        ]
        result, removed = deduplicate(lines)
        assert len(result) == 2
        assert removed == 0

    def test_different_markers_not_deduped(self):
        lines = [self.FakeLine("I", "SMITH, JOHN"), self.FakeLine("B", "SMITH, JOHN")]
        result, removed = deduplicate(lines)
        assert len(result) == 2

    def test_case_insensitive(self):
        lines = [self.FakeLine("I", "SMITH, JOHN"), self.FakeLine("I", "smith, john")]
        result, removed = deduplicate(lines)
        assert len(result) == 1
        assert removed == 1

    def test_three_same_one_different(self):
        lines = [
            self.FakeLine("I", "JONES, MARY"),
            self.FakeLine("I", "JONES, MARY"),
            self.FakeLine("I", "JONES, MARY ANN"),
        ]
        result, removed = deduplicate(lines)
        assert len(result) == 2
        assert removed == 1


# ===========================================================================
# Runner (when not using pytest)
# ===========================================================================
if __name__ == "__main__":
    import traceback

    classes = [
        TestI1, TestI2, TestI3, TestI4, TestI5,
        TestI6, TestI7, TestI8, TestI9, TestI10,
        TestApplyAllIRules, TestBRules, TestDedup,
    ]

    passed = 0
    failed = 0

    for cls in classes:
        instance = cls()
        methods = [m for m in dir(cls) if m.startswith("test_")]
        for method in methods:
            try:
                getattr(instance, method)()
                passed += 1
                print(f"  ✓ {cls.__name__}.{method}")
            except AssertionError as e:
                failed += 1
                print(f"  ✗ {cls.__name__}.{method}")
                print(f"      {e}")
            except Exception as e:
                failed += 1
                print(f"  ✗ {cls.__name__}.{method}")
                traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"{passed}/{passed+failed} tests passed")
    if failed:
        sys.exit(1)