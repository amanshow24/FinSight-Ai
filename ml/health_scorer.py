
def calculate_health_score(
    total_credit,
    total_debit,
    net_balance,
    anomaly_count,
    transaction_count,
    category_summary
):
    """
    Calculate 0-100 financial health score
    Returns: score, grade, tips
    """
    savings_rate = (
        net_balance / total_credit * 100
    ) if total_credit > 0 else 0

    if savings_rate >= 30:
        savings_score = 35
    elif savings_rate >= 20:
        savings_score = 28
    elif savings_rate >= 10:
        savings_score = 20
    elif savings_rate >= 0:
        savings_score = 10
    else:
        savings_score = 0

    anomaly_rate = (
        anomaly_count / transaction_count * 100
    ) if transaction_count > 0 else 0

    if anomaly_rate == 0:
        anomaly_score = 25
    elif anomaly_rate <= 2:
        anomaly_score = 20
    elif anomaly_rate <= 5:
        anomaly_score = 12
    elif anomaly_rate <= 10:
        anomaly_score = 5
    else:
        anomaly_score = 0

    total_spend = total_debit
    food_pct    = 0
    ent_pct     = 0

    if total_spend > 0:
        food_data = category_summary.get("Food", {})
        ent_data  = category_summary.get("Entertainment", {})
        food_pct  = food_data.get("percentage", 0)
        ent_pct   = ent_data.get("percentage", 0)

    if food_pct <= 30 and ent_pct <= 15:
        stability_score = 25
    elif food_pct <= 40 and ent_pct <= 25:
        stability_score = 18
    elif food_pct <= 50:
        stability_score = 10
    else:
        stability_score = 5

    if total_credit > total_debit * 1.3:
        budget_score = 15
    elif total_credit > total_debit:
        budget_score = 10
    elif total_credit == total_debit:
        budget_score = 5
    else:
        budget_score = 0
    total_score = (
        savings_score +
        anomaly_score +
        stability_score +
        budget_score
    )
    total_score = max(0, min(100, total_score))
    if total_score >= 85:
        grade = "A"
        grade_text = "Excellent"
    elif total_score >= 70:
        grade = "B"
        grade_text = "Good"
    elif total_score >= 55:
        grade = "C"
        grade_text = "Average"
    elif total_score >= 40:
        grade = "D"
        grade_text = "Needs Attention"
    else:
        grade = "F"
        grade_text = "Critical"
    tips = generate_tips(
        savings_rate, food_pct, ent_pct,
        anomaly_count, net_balance,
        category_summary
    )

    return {
        "score":          total_score,
        "grade":          grade,
        "grade_text":     grade_text,
        "savings_rate":   round(savings_rate, 1),
        "breakdown": {
            "savings_score":   savings_score,
            "anomaly_score":   anomaly_score,
            "stability_score": stability_score,
            "budget_score":    budget_score,
        },
        "tips": tips
    }


def generate_tips(
    savings_rate, food_pct, ent_pct,
    anomaly_count, net_balance,
    category_summary
):
    """Generate 3 personalized financial tips"""
    tips = []
    if savings_rate < 10:
        tips.append(
            "You're saving less than 10% of income. "
            "Try the 50-30-20 rule: "
            "50% needs, 30% wants, 20% savings."
        )
    elif savings_rate < 20:
        tips.append(
            " Good start! Increase savings to 20% "
            "by cutting one subscription or "
            "reducing dining out by 2x/week."
        )
    else:
        tips.append(
            " Great savings rate! Consider investing "
            "surplus in mutual funds via SIP "
            "for long-term wealth building."
        )

    if food_pct > 40:
        tips.append(
            f" Food is {food_pct}% of your spending — "
            "very high! Cook at home 3 more days/week "
            "to save ₹2000-4000/month."
        )
    elif food_pct > 30:
        tips.append(
            f"Food is {food_pct}% of spending. "
            "Reduce Zomato/Swiggy orders "
            "to max 3 times per week."
        )
    if ent_pct > 20:
        tips.append(
            f"Entertainment is {ent_pct}% of spending. "
            "Review your subscriptions — "
            "cancel unused ones to save ₹1000+/month."
        )
    if anomaly_count > 0:
        tips.append(
            f" {anomaly_count} suspicious transaction(s) detected. "
            "Review them immediately and contact "
            "your bank if unauthorized."
        )
    if net_balance < 0:
        tips.append(
            " You spent more than you earned this month! "
            "Create a strict budget for next month "
            "to avoid debt."
        )
    invest_data = category_summary.get("Investments", {})
    invest_pct  = invest_data.get("percentage", 0)
    if invest_pct == 0:
        tips.append(
            " No investments detected this month. "
            "Start a SIP with just ₹500/month "
            "on Groww or Zerodha to build wealth."
        )

    return tips[:3]