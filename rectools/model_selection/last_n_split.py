#  Copyright 2023 MTS (Mobile Telesystems)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""LastNSplitter."""

import typing as tp

import numpy as np
import pandas as pd

from rectools.dataset import Interactions
from rectools.model_selection.splitter import Splitter


class LastNSplitter(Splitter):
    """
    Generate train and test putting last n interaction for
    each user in test and others in train.
    It is also possible to exclude cold users and items
    and already seen items.

    Parameters
    ----------
    n: int
        Number of interactions for each user that will be included in test
    filter_cold_users: bool, default ``True``
        If `True`, users that not in train will be excluded from test.
    filter_cold_items: bool, default ``True``
        If `True`, items that not in train will be excluded from test.
    filter_already_seen: bool, default ``True``
        If ``True``, pairs (user, item) that are in train will be excluded from test.

    Examples
    --------
    >>> from rectools import Columns
    >>> df = pd.DataFrame(
    ...     [
    ...         [1, 1, 1, "2021-09-01"], # 0
    ...         [1, 2, 1, "2021-09-02"], # 1
    ...         [1, 1, 1, "2021-08-20"], # 2
    ...         [1, 2, 1, "2021-09-04"], # 3
    ...         [2, 1, 1, "2021-08-20"], # 4
    ...         [2, 2, 1, "2021-08-20"], # 5
    ...         [2, 3, 1, "2021-09-05"], # 6
    ...         [2, 2, 1, "2021-09-06"], # 7
    ...         [3, 1, 1, "2021-09-05"], # 8
    ...     ],
    ...     columns=[Columns.User, Columns.Item, Columns.Weight, Columns.Datetime],
    ... ).astype({Columns.Datetime: "datetime64[ns]"})
    >>> interactions = Interactions(df)
    >>>
    >>> lns = LastNSplitter(2, False, False, False)
    >>> for train_ids, test_ids, _ in lns.split(interactions):
    ...     print(train_ids, test_ids)
    [0 2 4 5] [1 3 6 7 8]
    >>>
    >>> lns = LastNSplitter(2, True, True, True)
    >>> for train_ids, test_ids, _ in lns.split(interactions):
    ...     print(train_ids, test_ids)
    [0 2 4 5] [1 3]
    """

    def __init__(
        self,
        n: int,
        filter_cold_users: bool = True,
        filter_cold_items: bool = True,
        filter_already_seen: bool = True,
    ) -> None:
        super().__init__()
        self.n = n
        self.filter_cold_users = filter_cold_users
        self.filter_cold_items = filter_cold_items
        self.filter_already_seen = filter_already_seen

    def _split_without_filter(
        self,
        interactions: Interactions,
        collect_fold_stats: bool = False,
    ) -> tp.Iterator[tp.Tuple[np.ndarray, np.ndarray, tp.Dict[str, tp.Any]]]:
        df = interactions.df
        idx = pd.RangeIndex(0, len(df))

        grouped_df = df.groupby("user_id")["datetime"].nlargest(self.n)
        test_interactions = grouped_df.keys().to_numpy()
        get_second_value = np.vectorize(lambda x: x[1])
        test_interactions = get_second_value(test_interactions)
        test_mask = np.zeros_like(idx, dtype=bool)
        test_mask[test_interactions] = True
        train_mask = ~test_mask

        train_idx = idx[train_mask].values
        test_idx = idx[test_mask].values

        fold_info = {}
        if collect_fold_stats:
            fold_info["n"] = self.n

        yield train_idx, test_idx, fold_info
