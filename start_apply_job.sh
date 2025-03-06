#!/bin/bash

links=(
    "https://jobs.workable.com/view/7ZLabkcPX4G2m9SBesq7Yd/hybrid-customer-success-and-product-manager-(1099-contract%2C-triive)-in-bentonville-at-high-alpha-innovation"
    "https://jobs.workable.com/view/beZTS1rb1b4EyK4Sf8jHUk/software-engineer-intern-in-phoenix-at-prepass%2C-llc"
    "https://jobs.workable.com/view/whUvBKiTvxCkYakHF82BdP/remote-senior-product-manager%2C-customer-service-in-united-states-at-jiffy"
    "https://jobs.workable.com/view/fCshFnHk3Z2Jy5uz7HFuWS/hybrid-senior-software-quality-assurance-engineer-in-san-diego-at-millennium-health"
    "https://jobs.workable.com/en/view/faeRjXdFxhAsdAsQZGSphe/senior-java-developer-(hybrid)-in-auburn-hills-at-detroit-labs"
    "https://jobs.workable.com/view/ru1nL4hqwaGhs8DwWKNpfU/remote-java-software-developer-(senior-level)-in-united-states-at-j-mack-technologies"
)

for link in "${links[@]}"; do
    python main.py --job-url "$link" --metadata-path "data/user_metadata.json"
    break # break for testing
done
