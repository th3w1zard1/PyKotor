# Setting Up GitHub Sponsors for OldRepublicDevs Organization

This guide will help you set up unified GitHub Sponsors for the OldRepublicDevs organization.

## Prerequisites

- You must be an organization owner (th3w1zard1 or NickHugi)
- Organization must be in a region supported by GitHub Sponsors
- Organization must contribute to open source projects

## Step-by-Step Setup

### 1. Navigate to GitHub Sponsors

1. Go to [https://github.com/sponsors](https://github.com/sponsors)
2. Click **"Get sponsored"** or visit [https://github.com/sponsors/accounts](https://github.com/sponsors/accounts)
3. Select **"OldRepublicDevs"** from the list of organizations

### 2. Complete Organization Profile

Fill out the required information:
- **Short bio**: Brief description of OldRepublicDevs (e.g., "Open source development organization maintaining PyKotor and related KOTOR tools")
- **Introduction**: Detailed description of the organization's mission and projects
- **Location**: Organization location (if applicable)
- **Website/Blog**: Organization website (if applicable)
- **Email**: Contact email for the organization

### 3. Choose Payment Method

You have two options:

#### Option A: Direct Bank Account (Recommended if available)
- Provide organization bank account details
- Complete tax forms (W-9 for US, or equivalent for your region)
- Funds go directly to organization account

#### Option B: Fiscal Host (Open Source Collective)
- If organization doesn't have a corporate bank account
- Use Open Collective as fiscal host
- Create a Collective on [Open Collective](https://opencollective.com)
- Select "This organization is using a fiscal host" during setup
- Choose "Open Source Collective" from the menu

### 4. Create Sponsorship Tiers

Define up to 10 monthly and 10 one-time sponsorship tiers:

**Example tiers:**
- **Bronze Sponsor** ($5/month): Name in README, early access to releases
- **Silver Sponsor** ($10/month): Bronze benefits + logo on website
- **Gold Sponsor** ($25/month): Silver benefits + priority support
- **Platinum Sponsor** ($50/month): Gold benefits + direct communication channel

For each tier, specify:
- Price (monthly or one-time)
- Description of benefits
- Optional: Welcome message
- Optional: Access to private repositories

### 5. Enable Two-Factor Authentication (2FA)

Ensure 2FA is enabled for the organization:
1. Go to Organization Settings → Security
2. Enable "Require two-factor authentication for all members"
3. Ensure all organization owners have 2FA enabled

### 6. Submit for Review

1. Review all information
2. Submit application to GitHub
3. Wait for approval (typically 1-3 business days)

### 7. Update FUNDING.yml

Once approved, the FUNDING.yml file should include the organization:

```yaml
github: [OldRepublicDevs, th3w1zard1, NickHugi]
```

The organization will appear first in the sponsor button, providing a unified funding option.

## Verification

After setup, verify the organization sponsors page:
- Visit: `https://github.com/sponsors/OldRepublicDevs`
- Should show organization profile and sponsorship tiers
- Sponsor button on repository should show organization option

## Troubleshooting

### Organization doesn't appear in sponsor button
- Ensure GitHub Sponsors is fully approved and active
- Check that FUNDING.yml includes `OldRepublicDevs`
- Clear browser cache and refresh

### Payment issues
- Verify bank account or fiscal host is properly configured
- Check tax forms are submitted and approved
- Contact GitHub Support if issues persist

## Resources

- [GitHub Sponsors Documentation](https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors/setting-up-github-sponsors-for-your-organization)
- [Open Collective Documentation](https://docs.oscollective.org/campaigns-and-partnerships/github-sponsors)
- [GitHub Sponsors Accounts](https://github.com/sponsors/accounts)

