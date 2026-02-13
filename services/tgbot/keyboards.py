"""Inline keyboard builders for Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def reading_actions_keyboard(
    reading_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Post-reading action buttons."""
    buttons: list[list[InlineKeyboardButton]] = []
    if reading_id:
        buttons.append(
            [
                InlineKeyboardButton(
                    "\U0001f4ca Full Details",
                    callback_data=f"reading:details:{reading_id}",
                ),
                InlineKeyboardButton(
                    "\u2b50 Rate",
                    callback_data=f"reading:rate:{reading_id}",
                ),
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "\U0001f4e4 Share",
                    callback_data=f"reading:share:{reading_id}",
                ),
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton("\U0001f52e New Reading", callback_data="reading:new"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def history_keyboard(
    readings: list[dict], has_more: bool, current_offset: int = 0
) -> InlineKeyboardMarkup:
    """History navigation keyboard with per-reading view buttons."""
    buttons: list[list[InlineKeyboardButton]] = []

    # Per-reading view buttons (2 per row)
    row: list[InlineKeyboardButton] = []
    for i, r in enumerate(readings):
        rid = r.get("id", 0)
        row.append(
            InlineKeyboardButton(f"View #{i + 1}", callback_data=f"history:view:{rid}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Load more button
    if has_more:
        next_offset = current_offset + len(readings)
        buttons.append(
            [
                InlineKeyboardButton(
                    "Load More \u25b6",
                    callback_data=f"history:more:{next_offset}",
                )
            ]
        )

    return InlineKeyboardMarkup(buttons)


def reading_type_keyboard() -> InlineKeyboardMarkup:
    """Choose reading type when user clicks 'New Reading'."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "\U0001f550 Time Reading", callback_data="reading:type:time"
                ),
                InlineKeyboardButton(
                    "\u2753 Question", callback_data="reading:type:question"
                ),
            ],
            [
                InlineKeyboardButton(
                    "\U0001f4db Name Reading", callback_data="reading:type:name"
                ),
                InlineKeyboardButton(
                    "\U0001f31f Daily Insight", callback_data="reading:type:daily"
                ),
            ],
        ]
    )
