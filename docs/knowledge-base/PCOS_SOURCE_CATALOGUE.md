# PCOS source candidates

Assessment date: 2026-11-04. This is a research catalogue, not approval for
ingestion or clinical use. No medical article text was added to the repository.
The registry contains WHO, Monash and the new FDA metadata candidate; all remain
ineligible for ingestion and production retrieval. Existing approvals were not
changed. `last_verified_date` records metadata checking, not clinical review.

| Candidate | Reuse assessment | Current disposition |
| --- | --- | --- |
| [WHO fact sheet](https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome), dated 22 January 2026 | [Website terms](https://www.who.int/about/policies/terms-of-use) distinguish limited private/noncommercial educational extracts from substantial reproduction requiring authorization. Do not assume that a WHO publication licence covers this web page. | Existing metadata only. Verify exact reuse rights and obtain clinical review before ingestion. |
| [FDA patient information](https://www.fda.gov/consumers/womens-health-topics/polycystic-ovary-syndrome-pcos) | [FDA website policy](https://www.fda.gov/about-fda/about-website/website-policies) generally permits reuse of public-domain material, with exceptions for identified third-party content. Check the specific text and preserve attribution. | Added as `fda-pcos`, development-only, permission unverified, not clinically reviewed, metadata only. No licence or approval inferred. |
| [PMC9964744](https://pmc.ncbi.nlm.nih.gov/articles/PMC9964744/), *Polycystic Ovary Syndrome: Etiology, Current Management, and Future Therapeutics*, Singh et al., 11 February 2023, DOI `10.3390/jcm12041454` | Indexed PMC article metadata identifies CC BY 4.0; preserve authors, title, DOI, licence and any modifications. Reconfirm the downloaded version's rights and third-party exceptions. Direct browser access encountered a CAPTCHA. Use [PMC's designated automated retrieval services](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/), without bypassing access controls. | Documentation candidate only. This broad review is not a systematic review or clinical guideline. Existing evidence enums lack an appropriate review type; a separately approved schema change is needed before registry admission. Experimental-treatment discussion also requires clinical selection. |
| [Medscape overview](https://emedicine.medscape.com/article/256806-overview) | Article and [terms](https://www.medscape.com/public/termsofuse) could not be accessed during checking. Current contents and reuse permission are unverified. | Link/reference only pending accessible permission evidence and review. No login/access-control bypass. |
| [SSM Health patient page](https://www.ssmhealth.com/services/womens-health/gynecology/polycystic-ovary-syndrome-pcos) | [Website terms](https://www.ssmhealth.com/privacy-notices-terms-of-use/website-terms-of-use) restrict automated downloading, reproduction and derivatives. Public readability does not grant ingestion rights. | Link/reference only unless explicit permission is obtained, then clinical review. |

The existing Monash guideline metadata remains unchanged. This task did not
reverify or authorize it. Neither a publisher's reputation nor open licensing is
a substitute for AfyaHer's qualified clinical review.

## Before real content enters the knowledge base

1. Record exact permission/licence evidence for the selected version, permitted
   use, attribution requirements and authorization date. Check automated access
   rules separately from copyright permission.
2. Obtain an actual qualified review of topic relevance, educational scope,
   currency and Kenya applicability. Record the real review decision; never have
   a model invent reviewer names, dates or approvals.
3. Agree how to preserve immutable source versions, original text, section
   locations, retrieval date and content fingerprints. Existing passage positions
   do not provide a source snapshot/version history. Any schema/dependency change
   needs approval under repository rules.
4. Only then fetch from an allowlisted official endpoint with bounded responses,
   preserve attribution, extract text deterministically, and use the existing
   eligibility checks and passage chunker. No medical fetcher is implemented here.
5. Production retrieval and the evidence provenance gate must still run. Passing
   provenance only permits future claim-support assessment; it cannot authorize
   answer generation.
