import json
from models import db, User, Target, Contract

def execute_payout(target_name, winning_duration):
    contracts = Contract.query.filter_by(target_name=target_name).all()

    for c in contracts:
        player = User.query.get(c.user_id)
        if player:
            if winning_duration == c.duration:
                player.balance += c.potential_payout
            elif winning_duration == "REFUND":
                player.balance += c.stake
        db.session.delete(c)

    target = Target.query.filter_by(name=target_name).first()
    if target:
        target.total_wagered = 0.0

        # NEW: Increase their mute count if it wasn't a false alarm
        if winning_duration != "REFUND":
            target.times_muted += 1

        # NEW: Recalculate their baseline odds for the next round.
        # The more they get muted, the lower their base multiplier becomes!
        mutes = target.times_muted
        new_odds = {
            "1h": max(1.1, round(3.0 - (mutes * 0.3), 2)),
            "24h": max(1.5, round(5.0 - (mutes * 0.5), 2)),
            "1w": max(2.0, round(8.0 - (mutes * 0.8), 2))
        }
        target.odds_json = json.dumps(new_odds)

    db.session.commit()
    return True
