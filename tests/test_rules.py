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

import pytest
from rules_i import (
    apply_i1, apply_i2, apply_i3, apply_i4, apply_i5,
    apply_i6, apply_i7, apply_i8, apply_i9, apply_i10,
    apply_all_i_rules, AmbiguousCase, ReclassifyAsB,
    apply_mc_prefix, apply_business_before_comma, apply_business_after_comma,
    check_hyphenated_business_before_comma, apply_maiden_name_rule,
    single_surname_only,
)
from rules_b import apply_all_b_rules, FlagForReview
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

    def test_empty_string(self):
        assert apply_i2("") is None

    def test_real_name_kept(self):
        assert apply_i2("SMITH, JOHN") == "SMITH, JOHN"

    def test_movant_not_deleted(self):
        # MOVANT is ambiguous — not auto-deleted, whole case goes to weird
        assert apply_i2("MOVANT, ") == "MOVANT, "

    def test_lienholder_not_deleted(self):
        # LIENHOLDER is ambiguous — not auto-deleted, whole case goes to weird
        assert apply_i2("LIENHOLDER,") == "LIENHOLDER,"

    def test_respondent_not_deleted(self):
        # RESPONDENT is ambiguous — not auto-deleted, whole case goes to weird
        assert apply_i2("RESPONDENT, ") == "RESPONDENT, "


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

    def test_an_adult_stripped(self):
        assert apply_i3("SMITH, JOHN AN ADULT") == "SMITH, JOHN"

    def test_in_re_adult_stripped(self):
        assert apply_i3("JONES, MARY IN RE ADULT") == "JONES, MARY"

    def test_in_re_an_adult_stripped(self):
        assert apply_i3("DOE, JANE IN RE AN ADULT") == "DOE, JANE"

    def test_guardian_of_stripped(self):
        assert apply_i3("SMITH, JOHN GUARDIAN OF") == "SMITH, JOHN"

    def test_as_guardian_of_stripped(self):
        assert apply_i3("JONES, MARY AS GUARDIAN OF") == "JONES, MARY"

    def test_guardian_ad_litem_stripped(self):
        assert apply_i3("DOE, JANE GUARDIAN AD LITEM") == "DOE, JANE"

    def test_as_guardian_ad_litem_of_stripped(self):
        assert apply_i3("DOE, JANE AS GUARDIAN AD LITEM OF") == "DOE, JANE"

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
        assert result == "COUNTY OF GRAYSON"
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
# Bug-fix regression tests
# ===========================================================================

class TestBugFixes:
    # --- rules_b.py: B-8 must NOT convert records with known business words to I ---

    def test_lumber_street_stays_b(self):
        """LUMBER is a business indicator — must not convert to I"""
        result, rule = apply_all_b_rules("LUMBER MAIN STREET")
        assert result == "LUMBER MAIN STREET"
        assert rule == "B-1"

    def test_fitness_usa_stays_b(self):
        """FITNESS is a business indicator — must not convert to I"""
        result, rule = apply_all_b_rules("FITNESS USA")
        assert result == "FITNESS USA"
        assert rule == "B-1"

    def test_cars_quality_used_moved(self):
        """CAR/CARS prefix must move to end via B-2"""
        result, rule = apply_all_b_rules("CARS QUALITY USED")
        assert result == "QUALITY USED CARS"
        assert rule == "B-2"

    def test_homes_a1_mobile_flagged(self):
        """Alphanumeric token A-1 must trigger FlagForReview"""
        with pytest.raises(FlagForReview):
            apply_all_b_rules("HOMES A-1 MOBILE")

    # --- rules_b.py: B-3 CITY OF pattern ---

    def test_city_of_moved_to_front(self):
        """VAN ALSTYNE CITY OF → CITY OF VAN ALSTYNE"""
        result, rule = apply_all_b_rules("VAN ALSTYNE CITY OF")
        assert result == "CITY OF VAN ALSTYNE"
        assert rule == "B-3"

    # --- rules_b.py: B-4 no-split for name ending with legal suffix ---

    def test_company_inc_not_split(self):
        """Name ending with INC must not be split even when AND is present"""
        result, rule = apply_all_b_rules("LANGFORD AND MONTGOMERY SURVEY COMPANY INC")
        assert result == "LANGFORD AND MONTGOMERY SURVEY COMPANY INC"
        assert rule == "B-1"

    # --- rules_b.py: B-4 flag when part has only single-letter tokens ---

    def test_single_letter_parts_flagged(self):
        """C P AND ASSOCIIATESINC — 'C P' is all single letters, must flag"""
        with pytest.raises(FlagForReview):
            apply_all_b_rules("C P AND ASSOCIIATESINC")

    # --- rules_b.py: B-5 WIFE pattern with single surname ---

    def test_wife_single_surname_stays_b(self):
        """HEROD AND WIFE STACYE → B: HEROD, STACYE"""
        result, rule = apply_all_b_rules("HEROD AND WIFE STACYE")
        assert result == [{"marker": "B", "name": "HEROD, STACYE"}]
        assert rule == "B-5"

    def test_wife_full_name_still_i(self):
        """Existing: MILLS JAMES E AND WIFE LINDA D MILLS still produces I records"""
        result, rule = apply_all_b_rules("MILLS JAMES E AND WIFE LINDA D MILLS")
        assert isinstance(result, list)
        assert all(r["marker"] == "I" for r in result)

    # --- rules_i.py: MC prefix ---

    def test_mc_prefix_joined(self):
        """MC, DADE WILLIE MAE → MCDADE, WILLIE MAE"""
        result = apply_mc_prefix("MC, DADE WILLIE MAE")
        assert result == "MCDADE, WILLIE MAE"

    def test_mac_prefix_joined(self):
        """MAC, DONALD JAMES → MACDONALD, JAMES"""
        result = apply_mc_prefix("MAC, DONALD JAMES")
        assert result == "MACDONALD, JAMES"

    def test_mc_prefix_in_pipeline(self):
        result, rule = apply_all_i_rules("MC, DADE WILLIE MAE")
        assert result == "MCDADE, WILLIE MAE"
        assert rule == "I-MC"

    # --- rules_i.py: business indicator before comma → B ---

    def test_manufacturer_before_comma_raises(self):
        """MANUFACTURER, JOHN DOOR → ReclassifyAsB with new_name 'JOHN DOOR MANUFACTURER'"""
        with pytest.raises(ReclassifyAsB) as exc:
            apply_business_before_comma("MANUFACTURER, JOHN DOOR")
        assert exc.value.new_name == "JOHN DOOR MANUFACTURER"

    # --- rules_i.py: business indicator after comma → swap ---

    def test_manufacturers_after_comma_swapped(self):
        """CONSOLIDATION, MANUFACTURERS → MANUFACTURERS CONSOLIDATION (stays I)"""
        result = apply_business_after_comma("CONSOLIDATION, MANUFACTURERS")
        assert result == "MANUFACTURERS CONSOLIDATION"

    def test_manufacturers_after_comma_in_pipeline(self):
        result, rule = apply_all_i_rules("CONSOLIDATION, MANUFACTURERS")
        assert result == "MANUFACTURERS CONSOLIDATION"
        assert rule == "I-BAC"

    # --- rules_i.py: game names → B ---

    def test_bingo_reclassified_as_b(self):
        """BINGO, has trailing comma → single surname only → AmbiguousCase for human review"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("BINGO,")

    # --- rules_i.py: short abbreviation → B ---

    def test_mci_short_abbreviation_b(self):
        """MCI, has trailing comma → single surname only → AmbiguousCase for human review"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("MCI,")

    # --- rules_i.py: hyphenated non-name → flag ---

    def test_hyphenated_nonname_flagged(self):
        """WHOPPER-STOPPER → AmbiguousCase"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("WHOPPER-STOPPER,")


# ===========================================================================
# New bug-fix regression tests (2026-03-26)
# ===========================================================================

class TestNewBugFixes:
    # Tiny stub that acts as a name DB for maiden-name tests
    class _DB:
        FIRST_NAMES = {"DEBORAH", "MARGARET", "MARY", "JANE", "ALICE", "SARAH", "LINDA"}

        def is_first_name(self, name: str) -> bool:
            return name.upper() in self.FIRST_NAMES

    # --- 1. Ambiguous hyphenated business name → flag ---

    def test_movers_miller_house_flagged(self):
        """MOVERS-MILLER, HOUSE → AmbiguousCase (MOVERS is a business word)"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("MOVERS-MILLER, HOUSE")

    def test_hyphenated_normal_name_not_flagged(self):
        """SMITH-JONES, MARY → no exception (no business word in hyphen)"""
        result, _ = apply_all_i_rules("SMITH-JONES, MARY")
        assert result == "SMITH-JONES, MARY"

    # --- 2. Business keyword before comma in I record → reclassify as B ---

    def test_yard_wrecking_reclassified_as_b(self):
        """YARD, EARL RATCLIFF WRECKING → ReclassifyAsB('EARL RATCLIFF WRECKING YARD')"""
        with pytest.raises(ReclassifyAsB) as exc:
            apply_all_i_rules("YARD, EARL RATCLIFF WRECKING")
        assert exc.value.new_name == "EARL RATCLIFF WRECKING YARD"

    def test_church_before_comma_reclassified_as_b(self):
        """CHURCH, OPEN DOOR DEL APOSTOLIC → ReclassifyAsB"""
        with pytest.raises(ReclassifyAsB) as exc:
            apply_all_i_rules("CHURCH, OPEN DOOR DEL APOSTOLIC")
        assert exc.value.new_name == "OPEN DOOR DEL APOSTOLIC CHURCH"

    def test_club_before_comma_reclassified_as_b(self):
        """CLUB, BANSHEE MOTORCYCLE → ReclassifyAsB"""
        with pytest.raises(ReclassifyAsB) as exc:
            apply_all_i_rules("CLUB, BANSHEE MOTORCYCLE")
        assert exc.value.new_name == "BANSHEE MOTORCYCLE CLUB"

    def test_council_before_comma_reclassified_as_b(self):
        """COUNCIL, DENISON CITY → ReclassifyAsB"""
        with pytest.raises(ReclassifyAsB) as exc:
            apply_all_i_rules("COUNCIL, DENISON CITY")
        assert exc.value.new_name == "DENISON CITY COUNCIL"

    # --- 3. Maiden name appended at end → hyphenated surname ---

    def test_maiden_name_appended(self):
        """GARNER, DEBORAH MARGARET ROGERS → ROGERS-GARNER, DEBORAH MARGARET"""
        result, _ = apply_all_i_rules("GARNER, DEBORAH MARGARET ROGERS", db=self._DB())
        assert result == "ROGERS-GARNER, DEBORAH MARGARET"

    def test_maiden_name_rule_skipped_when_second_not_first_name(self):
        """SMITH, MARY ROGERS JONES — second token ROGERS not a confirmed first name, no transform"""
        result, _ = apply_all_i_rules("SMITH, MARY ROGERS JONES", db=self._DB())
        assert result == "SMITH, MARY ROGERS JONES"

    def test_maiden_name_rule_skipped_on_suffix(self):
        """CHAMBERS, MARY JANE JR — JR is a suffix, no maiden-name transform"""
        result, _ = apply_all_i_rules("CHAMBERS, MARY JANE JR", db=self._DB())
        assert result == "CHAMBERS, MARY JANE JR"

    # --- 4. ASSOCIATES prefix in B record moves to end ---

    def test_county_of_moved_to_front(self):
        """GRAYSON COUNTY OF → COUNTY OF GRAYSON (not drop OF)"""
        result, rule = apply_all_b_rules("GRAYSON COUNTY OF")
        assert result == "COUNTY OF GRAYSON"
        assert rule == "B-3"

    def test_associates_prefix_moved_to_end(self):
        """ASSOCIATES DONALD L JARVIS AND → DONALD L JARVIS AND ASSOCIATES"""
        result, rule = apply_all_b_rules("ASSOCIATES DONALD L JARVIS AND")
        assert result == "DONALD L JARVIS AND ASSOCIATES"
        assert rule == "B-2"


# ===========================================================================
# Bug fixes 2026-03-27
# ===========================================================================

class TestBugFixes20260327:

    # Bug 1: APPAREL prefix moves to end via B-2
    def test_apparel_prefix_moved_to_end(self):
        """APPAREL S AND K → S AND K APPAREL (B-2)"""
        result, rule = apply_all_b_rules("APPAREL S AND K")
        assert result == "S AND K APPAREL"
        assert rule == "B-2"

    # Bug 3: EXTRIX EST stripped from I records via I-3
    def test_extrix_est_stripped(self):
        """SCHNITKER, EXTRIX EST EUGENE → SCHNITKER, EUGENE (I-3)"""
        result = apply_i3("SCHNITKER, EXTRIX EST EUGENE")
        assert result == "SCHNITKER, EUGENE"

    # Bug 4: INDV AS stripped, then Case D splits into two I records
    def test_indv_as_split_into_i_records(self):
        """SCHNITKER RONALD J AND DOROTHY JEAN INDV AS → two I records (B-5)"""
        result, rule = apply_all_b_rules("SCHNITKER RONALD J AND DOROTHY JEAN INDV AS")
        assert rule == "B-5"
        assert result == [
            {"marker": "I", "name": "SCHNITKER, RONALD J"},
            {"marker": "I", "name": "SCHNITKER, DOROTHY JEAN"},
        ]

    # Bug 5: SEAFOOD records are never split on AND
    def test_seafood_not_split(self):
        """SEAFOOD J AND J → unchanged, B-1 (no split)"""
        result, rule = apply_all_b_rules("SEAFOOD J AND J")
        assert result == "SEAFOOD J AND J"
        assert rule == "B-1"

# ===========================================================================
# Currency / monetary term detection
# ===========================================================================

class TestCurrencyDetection:
    """Tests for contains_currency_terms() — standalone token matching only."""

    @classmethod
    def setup_class(cls):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    def _check(self, name: str) -> bool:
        from main import contains_currency_terms
        return contains_currency_terms(name)

    def test_cents_triggers(self):
        assert self._check("CENTS FIVE HUNDRED TWENTY-EIGHT DOLLARS AND SEVENTY") is True

    def test_dollars_triggers(self):
        assert self._check("FIVE HUNDRED DOLLARS AND NO CENTS") is True

    def test_us_currency_triggers(self):
        assert self._check("ZIRCONIA IN US CURRENCY AND SIX CUBIC") is True

    def test_seized_currency_triggers(self):
        assert self._check("SEIZED CURRENCY") is True

    def test_money_triggers(self):
        assert self._check("MONEY DAMAGES AMOUNT") is True

    def test_cash_triggers(self):
        assert self._check("CASH PROCEEDS FORFEITED") is True

    def test_funds_triggers(self):
        assert self._check("FUNDS HELD IN TRUST") is True

    def test_proceeds_triggers(self):
        assert self._check("PROCEEDS OF SALE") is True

    def test_seize_triggers(self):
        assert self._check("SEIZE ALL ASSETS") is True

    def test_seizure_triggers(self):
        assert self._check("SEIZURE OF PROPERTY") is True

    def test_dollard_surname_not_triggered(self):
        """DOLLARD is a surname — DOLLARS token not present."""
        assert self._check("DOLLARD, JAMES") is False

    def test_centsmith_surname_not_triggered(self):
        """CENTSMITH is a surname — CENTS token not present."""
        assert self._check("CENTSMITH, MARY") is False

    def test_plain_name_not_triggered(self):
        assert self._check("SMITH, JOHN") is False


# ===========================================================================
# AND WIFE + legal suffix detection
# ===========================================================================

class TestAndWifeDetection:
    """Tests for contains_and_wife_legal() — AND WIFE with legal suffix detection."""

    @classmethod
    def setup_class(cls):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    def _check(self, name: str) -> bool:
        from main import contains_and_wife_legal
        return contains_and_wife_legal(name)

    def test_winkler_triggers(self):
        """AND WIFE followed by IND AND and A-N-F → weird"""
        assert self._check("WINKLER CHARLES K AND WIFE CAROL WINKLER IND AND A-N-F O") is True

    def test_davis_triggers(self):
        """AND WIFE followed by IND AND → weird"""
        assert self._check("DAVIS DON AND WIFE SUSIE DAVIS IND AND") is True

    def test_smith_bare_triggers(self):
        """Bare AND WIFE at end (no name after) → weird"""
        assert self._check("SMITH JOHN AND WIFE") is True

    def test_mills_not_triggered(self):
        """Clean B-5 pattern: AND WIFE FIRSTNAME SURNAME → not flagged"""
        assert self._check("MILLS JAMES E AND WIFE LINDA D MILLS") is False

    def test_midwife_not_triggered(self):
        """MIDWIFE does not contain standalone AND WIFE phrase"""
        assert self._check("MIDWIFE MEDICAL CENTER") is False


# ===========================================================================
# Non-name content detection
# ===========================================================================

class TestNonNameDetection:
    """Tests for is_non_name_content() — conservative non-name detection."""

    @classmethod
    def setup_class(cls):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    def _check(self, name: str) -> bool:
        from main import is_non_name_content
        return is_non_name_content(name)

    # --- Lines that MUST trigger ---

    def test_double_dash_plaintiff_defendant_triggers(self):
        """PLAINTIFF-- --DEFENDANT AND THIRD PARTY → flagged (double dash)"""
        assert self._check("PLAINTIFF-- --DEFENDANT AND THIRD PARTY") is True

    def test_double_dash_defendant_plaintiff_triggers(self):
        """DEFENDANT--PLAINTIFF → flagged (double dash)"""
        assert self._check("DEFENDANT--PLAINTIFF") is True

    def test_restaurants_single_word_triggers(self):
        """RESTAURANTS (single generic word) → flagged"""
        assert self._check("RESTAURANTS") is True

    def test_firearms_single_word_triggers(self):
        """FIREARMS (single generic word) → flagged"""
        assert self._check("FIREARMS") is True

    def test_defendant_exact_role_triggers(self):
        """DEFENDANT (pure role label) → flagged"""
        assert self._check("DEFENDANT") is True

    def test_plaintiff_exact_role_triggers(self):
        """PLAINTIFF (pure role label) → flagged"""
        assert self._check("PLAINTIFF") is True

    def test_third_party_exact_role_triggers(self):
        """THIRD PARTY (pure role phrase) → flagged"""
        assert self._check("THIRD PARTY") is True

    def test_unknown_parties_triggers(self):
        """UNKNOWN PARTIES → flagged"""
        assert self._check("UNKNOWN PARTIES") is True

    def test_all_persons_triggers(self):
        """ALL PERSONS → flagged"""
        assert self._check("ALL PERSONS") is True

    def test_unknown_heirs_triggers(self):
        """UNKNOWN HEIRS (standalone) → flagged"""
        assert self._check("UNKNOWN HEIRS") is True

    # --- Lines that must NOT trigger ---

    def test_hull_david_and_associates_not_triggered(self):
        """HULL DAVID AND ASSOCIATES → valid business name, not flagged"""
        assert self._check("HULL DAVID AND ASSOCIATES") is False

    def test_corroon_and_black_not_triggered(self):
        """CORROON AND BLACK → valid law firm, not flagged"""
        assert self._check("CORROON AND BLACK") is False

    def test_cable_post_newsweek_not_triggered(self):
        """CABLE, POST-NEWSWEEK → valid I record, not flagged"""
        assert self._check("CABLE, POST-NEWSWEEK") is False

    def test_restaurants_garcia_not_triggered(self):
        """RESTAURANTS GARCIA → has a proper noun, not flagged"""
        assert self._check("RESTAURANTS GARCIA") is False

    def test_foltz_roger_not_triggered(self):
        """FOLTZ, ROGER → plain person name, not flagged"""
        assert self._check("FOLTZ, ROGER") is False

    def test_lexington_insurance_company_not_triggered(self):
        """LEXINGTON INSURANCE COMPANY → valid business, not flagged"""
        assert self._check("LEXINGTON INSURANCE COMPANY") is False


# ===========================================================================
# Integration test: flagged.txt output
# ===========================================================================
class TestFlaggedTxt:
    """Verify that running the pipeline produces FILENAME_flagged.txt."""

    def test_flagged_txt_created_alongside_json(self, tmp_path):
        import sys
        from unittest.mock import patch

        # Build a minimal input: one clean case + one that triggers FlagForReview
        # (B record with alphanumeric token reliably raises FlagForReview)
        input_dir = tmp_path / "data" / "input"
        input_dir.mkdir(parents=True)
        input_file = input_dir / "test_flagged_output.txt"
        input_file.write_text(
            # clean case
            "19880101\t000001    \tJDG\t02\tTEST CASE\t\t\n"
            "19880101\t000001    \tJDG\t04\tI\tSMITH, JOHN\t\n"
            # flagged case: B record with alphanumeric token (e.g. "UNIT2")
            "19880102\t000002    \tJDG\t02\tTEST CASE 2\t\t\n"
            "19880102\t000002    \tJDG\t04\tB\tACME UNIT2 INC\t\n",
            encoding="utf-8",
        )

        output_dir = tmp_path / "data" / "output"
        flagged_dir = tmp_path / "data" / "flagged"
        output_dir.mkdir(parents=True)
        flagged_dir.mkdir(parents=True)

        src_dir = Path(__file__).parent.parent / "src"
        with patch("sys.argv", ["main.py", str(input_file)]):
            import importlib, os
            old_cwd = os.getcwd()
            os.chdir(tmp_path)
            try:
                import main as main_mod
                importlib.reload(main_mod)
                main_mod.main()
            finally:
                os.chdir(old_cwd)

        json_path = flagged_dir / "test_flagged_output_flagged.json"
        txt_path  = flagged_dir / "test_flagged_output_flagged.txt"

        assert json_path.exists(), "flagged.json was not created"
        assert txt_path.exists(),  "flagged.txt was not created"

        content = txt_path.read_text(encoding="utf-8")
        assert "000002" in content, "flagged case_number not found in .txt"
        assert "ACME UNIT2 INC" in content, "flagged name not found in .txt"
        # clean case must NOT appear in flagged.txt
        assert "000001" not in content, "clean case should not appear in .txt"


# ===========================================================================
# Single surname only (I-SS)
# ===========================================================================
class TestSingleSurnameOnly:
    """Tests for single_surname_only() and its integration in apply_all_i_rules."""

    def test_bingo_comma_triggers(self):
        """BINGO, has no first name → single_surname_only returns True"""
        assert single_surname_only("BINGO,") is True

    def test_smith_trailing_space_triggers(self):
        """SMITH,  (trailing space) has no first name → triggers"""
        assert single_surname_only("SMITH, ") is True

    def test_smith_john_not_triggered(self):
        """SMITH, JOHN has a first name → not caught"""
        assert single_surname_only("SMITH, JOHN") is False

    def test_respondent_not_triggered(self):
        """RESPONDENT is a role label — not caught by this rule"""
        assert single_surname_only("RESPONDENT, ") is False

    def test_bare_comma_not_triggered(self):
        """, (just a comma/space) — handled by I-2, not this rule"""
        assert single_surname_only(", ") is False

    def test_bingo_raises_ambiguous_in_pipeline(self):
        """BINGO, through apply_all_i_rules → AmbiguousCase (single surname)"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("BINGO,")

    def test_smith_comma_raises_ambiguous_in_pipeline(self):
        """SMITH, through apply_all_i_rules → AmbiguousCase (single surname)"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("SMITH,")


# ===========================================================================
# "IND AND AS NEXT FRIEND OF/FOR" — legal role fragment guard
# ===========================================================================
class TestNextFriendGuard:
    def test_b_ind_and_next_friend_of_flagged(self):
        """B record with IND AND AS NEXT FRIEND OF → FlagForReview"""
        with pytest.raises(FlagForReview):
            apply_all_b_rules("THOMAS NANCY IND AND AS NEXT FRIEND OF JERRY")

    def test_b_individually_next_friend_of_flagged(self):
        """B record with INDIVIDUALLY AND AS NEXT FRIEND OF → FlagForReview"""
        with pytest.raises(FlagForReview):
            apply_all_b_rules("JONES MARY INDIVIDUALLY AND AS NEXT FRIEND OF BILLY")

    def test_b_ind_and_next_friend_for_flagged(self):
        """B record with IND AND AS NEXT FRIEND FOR → FlagForReview"""
        with pytest.raises(FlagForReview):
            apply_all_b_rules("SMITH JAMES IND AND AS NEXT FRIEND FOR SUE")

    def test_b_no_regression_acme(self):
        """ACME CORPORATION is a plain business — not triggered"""
        result, rule = apply_all_b_rules("ACME CORPORATION")
        assert result == "ACME CORPORATION"

    def test_i_ind_and_next_friend_of_flagged(self):
        """I record with IND AND AS NEXT FRIEND OF → AmbiguousCase"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("THOMAS NANCY IND AND AS NEXT FRIEND OF JERRY")

    def test_i_individually_next_friend_for_flagged(self):
        """I record with INDIVIDUALLY AND AS NEXT FRIEND FOR → AmbiguousCase"""
        with pytest.raises(AmbiguousCase):
            apply_all_i_rules("DOE JANE INDIVIDUALLY AND AS NEXT FRIEND FOR BILLY")


# ===========================================================================
# Exact weird-name triggers
# ===========================================================================
class TestExactWeirdNames:
    def test_i_texas_savings_of(self):
        try:
            apply_all_i_rules("TEXAS, SAVINGS OF")
            assert False, "expected AmbiguousCase"
        except AmbiguousCase:
            pass

    def test_i_defendant_no(self):
        try:
            apply_all_i_rules("DEFENDANT, NO")
            assert False, "expected AmbiguousCase"
        except AmbiguousCase:
            pass

    def test_i_defendant_none(self):
        try:
            apply_all_i_rules("DEFENDANT, NONE")
            assert False, "expected AmbiguousCase"
        except AmbiguousCase:
            pass

    def test_i_plaintiff_defendant(self):
        try:
            apply_all_i_rules("PLAINTIFF--, --DEFENDANT")
            assert False, "expected AmbiguousCase"
        except AmbiguousCase:
            pass

    def test_i_defendant_john_no_raise(self):
        result, _ = apply_all_i_rules("DEFENDANT, JOHN")
        assert result is not None

    def test_i_smith_john_no_raise(self):
        result, _ = apply_all_i_rules("SMITH, JOHN")
        assert result is not None

    def test_b_texas_savings_of(self):
        try:
            apply_all_b_rules("TEXAS, SAVINGS OF")
            assert False, "expected FlagForReview"
        except FlagForReview:
            pass

    def test_b_plaintiff_defendant(self):
        try:
            apply_all_b_rules("PLAINTIFF--, --DEFENDANT")
            assert False, "expected FlagForReview"
        except FlagForReview:
            pass

    def test_b_smith_john_no_raise(self):
        result, _ = apply_all_b_rules("SMITH JOHN")
        assert result is not None


# ===========================================================================
# TestMergeNoDuplicates
# ===========================================================================
class TestMergeNoDuplicates:
    """Verify that merge_corrections never writes the same case_number twice."""

    def test_weird_dedup_same_case_multiple_entries(self):
        """A case with 3 weird entries must appear exactly once in weird_blocks."""
        import tempfile, os
        from main import merge_corrections

        raw_line = "19900101\t900001    \tJDG\t02\tTEST\t\t\n"
        flagged_line_1 = "19900101\t900001    \tJDG\t04\tI\tFOO,\t"
        flagged_line_2 = "19900101\t900001    \tJDG\t04\tI\tBAR,\t"
        flagged_line_3 = "19900101\t900001    \tJDG\t05\tI\tBAZ,\t"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "test.txt"
            output_path = tmp / "test_clean.txt"
            flagged_path = tmp / "test_flagged.json"
            flagged_txt_path = tmp / "test_flagged.txt"
            corrections_path = tmp / "test_corrections.json"
            review_path = tmp / "test_reviewCases.txt"

            # Write minimal input file (raw block)
            input_path.write_text(
                raw_line +
                f"19900101\t900001    \tJDG\t04\tI\tFOO,\t\n" +
                f"19900101\t900001    \tJDG\t04\tI\tBAR,\t\n" +
                f"19900101\t900001    \tJDG\t05\tI\tBAZ,\t\n",
                encoding="utf-8"
            )

            # Write flagged.json
            import json
            flagged_path.write_text(json.dumps([
                {"case_number": "900001", "original_marker": "I", "original_name": "FOO,",
                 "reason": "single surname with no first name: 'FOO,'",
                 "header_line": raw_line.strip(), "flagged_line": flagged_line_1},
                {"case_number": "900001", "original_marker": "I", "original_name": "BAR,",
                 "reason": "single surname with no first name: 'BAR,'",
                 "header_line": raw_line.strip(), "flagged_line": flagged_line_2},
                {"case_number": "900001", "original_marker": "I", "original_name": "BAZ,",
                 "reason": "single surname with no first name: 'BAZ,'",
                 "header_line": raw_line.strip(), "flagged_line": flagged_line_3},
            ]), encoding="utf-8")

            # Write flagged.txt (processed block with >>> on all three lines)
            flagged_txt_path.write_text(
                raw_line +
                f">>>{flagged_line_1}\n" +
                f">>>{flagged_line_2}\n" +
                f">>>{flagged_line_3}\n" +
                "\n",
                encoding="utf-8"
            )

            # Write corrections.json with 3 weird entries for the same case
            corrections_path.write_text(json.dumps([
                {"case_number": "900001", "flagged_line": flagged_line_1, "action": "weird"},
                {"case_number": "900001", "flagged_line": flagged_line_2, "action": "weird"},
                {"case_number": "900001", "flagged_line": flagged_line_3, "action": "weird"},
            ]), encoding="utf-8")

            output_path.write_text("", encoding="utf-8")

            merge_corrections(input_path, output_path, flagged_path, corrections_path)

            # reviewCases must contain the block exactly once
            review_text = review_path.read_text(encoding="utf-8")
            case_nums = [l.split("\t")[1].strip() for l in review_text.splitlines()
                         if "\t" in l and not l.startswith("#")]
            count = case_nums.count("900001")
            assert count > 0, "case 900001 was never written to reviewCases"
            lines_per_block = 4  # header + 3 data lines
            assert count == lines_per_block, (
                f"expected case 900001 to appear {lines_per_block} times "
                f"(1 block × {lines_per_block} lines), got {count}"
            )

    def test_weird_idempotent_second_run(self):
        """Running merge_corrections twice must not duplicate weird blocks."""
        import tempfile, json
        from main import merge_corrections

        raw_line = "19900101\t900002    \tJDG\t02\tTEST\t\t\n"
        flagged_line = "19900101\t900002    \tJDG\t04\tI\tFOO,\t"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path  = tmp / "test.txt"
            output_path = tmp / "test_clean.txt"
            flagged_path = tmp / "test_flagged.json"
            flagged_txt_path = tmp / "test_flagged.txt"
            corrections_path = tmp / "test_corrections.json"
            review_path = tmp / "test_reviewCases.txt"

            input_path.write_text(
                raw_line + f"19900101\t900002    \tJDG\t04\tI\tFOO,\t\n",
                encoding="utf-8"
            )
            flagged_path.write_text(json.dumps([
                {"case_number": "900002", "original_marker": "I", "original_name": "FOO,",
                 "reason": "single surname with no first name: 'FOO,'",
                 "header_line": raw_line.strip(), "flagged_line": flagged_line},
            ]), encoding="utf-8")
            flagged_txt_path.write_text(
                raw_line + f">>>{flagged_line}\n\n", encoding="utf-8"
            )
            corrections_path.write_text(json.dumps([
                {"case_number": "900002", "flagged_line": flagged_line, "action": "weird"},
            ]), encoding="utf-8")
            output_path.write_text("", encoding="utf-8")

            merge_corrections(input_path, output_path, flagged_path, corrections_path)
            merge_corrections(input_path, output_path, flagged_path, corrections_path)

            review_text = review_path.read_text(encoding="utf-8")
            case_nums = [l.split("\t")[1].strip() for l in review_text.splitlines()
                         if "\t" in l]
            count = case_nums.count("900002")
            assert count == 2, (
                f"expected 2 lines (1 block of 2 lines) for case 900002, got {count}"
            )


# ===========================================================================
# Runner (when not using pytest)
# ===========================================================================
if __name__ == "__main__":
    import traceback

    classes = [
        TestI1, TestI2, TestI3, TestI4, TestI5,
        TestI6, TestI7, TestI8, TestI9, TestI10,
        TestApplyAllIRules, TestBRules, TestDedup, TestBugFixes, TestNewBugFixes,
        TestNextFriendGuard,
        TestBugFixes20260327, TestCurrencyDetection, TestAndWifeDetection,
        TestSingleSurnameOnly, TestExactWeirdNames,
        TestMergeNoDuplicates,
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