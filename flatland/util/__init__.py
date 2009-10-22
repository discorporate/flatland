"""Utilities."""
import sys


type(sys.modules['flatland']).shadow(
    'flatland.util',
    {
        'base': (
            'Maybe',
            'Unspecified',
            'adict',
            'as_mapping',
            'assignable_class_property',
            'assignable_property',
            'class_cloner',
            'decorator',
            'format_argspec_plus',
            'keyslice_pairs',
            'lazy_property',
            'luhn10',
            'named_int_factory',
            're_ucompile',
            'symbol',
            'threading',
            'to_pairs',
            ),
        'signals': (
            'Signal',
            'signal',
            ),
      })
